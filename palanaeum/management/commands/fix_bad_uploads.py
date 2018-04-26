import logging
import os
import subprocess

from django.core.management.base import BaseCommand

from palanaeum.cloud import get_cloud_backend
from palanaeum.configuration import get_config
from palanaeum.models import AudioSource, Snippet, Entry, EntryLine, EntryVersion

from palanaeum.cloud.exceptions import DownloadError

logger = logging.getLogger('palanaeum.admin')


sources = AudioSource.objects.filter(raw_file__contains='(')
b2 = get_cloud_backend()
for source in sources:
    try:
        b2.download_file(b2._url_encode(source.raw_file), source.raw_file.path)
    except DownloadError:
        b2.download_file(source.raw_file, source.raw_file.path)

import subprocess
for source in sources:
    print(source)
    subprocess.run(
                ["ffmpeg", "-y", "-i", str(source.raw_file.path), "-b:a",
                 get_config('audio_quality'),
                 str(source.transcoded_file.path)],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                check=True)


cnt = Snippet.objects.filter(source__in=sources).count()
for i, snippet in enumerate(Snippet.objects.filter(source__in=sources), start=1):
    print("\tTranscoding snippet {}/{}...".format(i, cnt))
    subprocess.run(["ffmpeg", "-y", "-ss", str(snippet.beginning), "-i",
                    str(snippet.source.file.path),
                    "-t", str(snippet.length), str(snippet.file)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=True)

for source in sources:
    source.status = AudioSource.READY
    b2.upload_source(source)

for source in sources:
    print(source.event_id)

print({source.event_id for source in sources})

sources.update(status=AudioSource.READY)
for source in sources:
    os.unlink(source.raw_file.path)



entries = {line.entry_version.entry for line in EntryLine.objects.filter(speaker='Footnote')}


for entry in entries:
    version = entry.versions.last()
    assert(isinstance(version, EntryVersion))
    footnote = version.lines.filter(speaker='Footnote').first()
    if not footnote:
        continue
    assert (isinstance(footnote, EntryLine))
    version.archive_version()
    print(entry.id, footnote)
    version.note = footnote.text
    footnote.delete()
    version.save()
