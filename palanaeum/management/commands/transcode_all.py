import logging
import os
import subprocess

from django.core.management.base import BaseCommand

from palanaeum.cloud import get_cloud_backend
from palanaeum.configuration import get_config
from palanaeum.models import AudioSource, Snippet

logger = logging.getLogger('palanaeum.admin')


class Command(BaseCommand):
    help = 'Recode all audio files from source files.'

    def handle(self, *args, **options):
        audio_sources = AudioSource.objects.all()
        cnt = audio_sources.count()
        self.stdout.write("Starting to transcode {} audio sources.".format(cnt))
        logger.info("Starting to transcode %s audio sources.", cnt)
        for i, audio_source in enumerate(audio_sources, start=1):
            self.stdout.write("\tTranscoding source {}/{}: {}".format(
                i, cnt, audio_source.title
            ))
            logger.debug("Transcoding source %s/%s: %s", i, cnt,
                         audio_source.title)
            if not os.path.isfile(audio_source.raw_file.path) and audio_source.status == AudioSource.STORED_IN_CLOUD:
                try:
                    cloud = get_cloud_backend()
                    cloud.download_source(audio_source)
                except Exception as e:
                    logger.exception(str(e))
                    continue
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(audio_source.raw_file.path), "-b:a",
                 get_config('audio_quality'),
                 str(audio_source.transcoded_file.path)],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                check=True)
            if audio_source.status == AudioSource.STORED_IN_CLOUD:
                os.unlink(audio_source.raw_file.path)

        self.stdout.write("Successfully transcoded {} sources.".format(cnt))
        logger.info("Successfully transcoded %s sources.", cnt)

        snippets = Snippet.objects.select_related('source').all()
        cnt = snippets.count()
        self.stdout.write("Starting to transcode {} snippets.".format(cnt))
        logger.info("Starting to transcode %s snippets.", cnt)

        for i, snippet in enumerate(snippets, start=1):
            self.stdout.write("\tTranscoding snippet {}/{}...".format(i, cnt))
            logger.debug("Transcoding snippet %s/%s", i, cnt)
            subprocess.run(["ffmpeg", "-y", "-ss", str(snippet.beginning), "-i",
                            str(snippet.source.file.path),
                            "-t", str(snippet.length), str(snippet.file)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True)
        self.stdout.write("Successfully transcoded {} snippets.".format(cnt))
        logger.info("Successfully transcoded %s snippets.", cnt)
        self.stdout.write("Done.")
        return
