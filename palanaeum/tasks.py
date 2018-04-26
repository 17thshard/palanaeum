# coding=utf-8
import datetime
import logging
import os.path
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
import zipfile

from django.conf import settings
from django.core import management

from palanaeum.celery import app
from palanaeum.cloud import get_cloud_backend
from palanaeum.cloud.exceptions import PalanaeumCloudError
from palanaeum.configuration import get_config
from palanaeum.models import AudioSource, Snippet

logger = logging.getLogger('palanaeum.celery')


@app.task(ignore_result=True)
def transcode_source(audio_source_id: int):
    """
    Transcode the uploaded file to MP3 constant bit rate format.
    This will prevent issues with browsers wrongly estimating big audio file
    duration.
    """
    try:
        audio_source = AudioSource.objects.get(pk=audio_source_id)
    except AudioSource.DoesNotExist:
        logger.info("Didn't find AudioSource %s in database, maybe it wasn't committed yet. "
                    "Retrying in 2 seconds...", audio_source_id)
        time.sleep(2)
        try:
            logger.info("Trying again to find AudioSource %s...", audio_source_id)
            audio_source = AudioSource.objects.get(pk=audio_source_id)
        except AudioSource.DoesNotExist:
            logger.error("AudioSource %s wasn't found in the database.", audio_source_id)
            return

    if audio_source.status != AudioSource.WAITING:
        logger.error("AudioSource %s is not waiting to be processed. Aborting.", audio_source_id)
        return

    if not os.path.isfile(audio_source.raw_file.path) and audio_source.status == AudioSource.STORED_IN_CLOUD:
        cloud = get_cloud_backend()
        cloud.download_source(audio_source)

    if not os.path.isfile(audio_source.raw_file.path):
        logger.error("Raw file for %s is missing!", audio_source)

    path, ext = os.path.splitext(str(audio_source.raw_file))

    new_path = path + '.mp3'
    new_full_path = os.path.join(settings.MEDIA_ROOT, new_path)
    i = 1
    while os.path.exists(new_full_path):
        new_path = "".join([path] + ['-transcoded'] * i + ['.mp3'])
        i += 1
        new_full_path = os.path.join(settings.MEDIA_ROOT, new_path)

    try:
        audio_source.status = AudioSource.PROCESSING
        audio_source.save()

        logger.info("Starting to transcode AudioSource %s - %s.", audio_source_id, audio_source.title)
        subprocess.run(["ffmpeg", "-y", "-i", str(audio_source.file.path), "-b:a", get_config('audio_quality'),
                        str(new_full_path)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)

        audio_source.transcoded_file = str(new_path)
        # Make sure that the file wasn't deleted.
        if not AudioSource.objects.filter(pk=audio_source_id).exists():
            logger.error("The AudioSource %s has been deleted, before transcoding was completed.", audio_source_id)
            return
        audio_source.status = AudioSource.READY
        audio_source.save()
    except Exception as e:
        logger.exception("Failed to transcode AudioSource %s!", audio_source_id)
        audio_source.status = AudioSource.FAILED
        audio_source.save()
        raise e
    finally:
        if audio_source.status == AudioSource.STORED_IN_CLOUD and not get_config('audio_keep_original_file'):
            os.unlink(audio_source.raw_file.path)

    logger.info("Transcoding of AudioSource %s finished.", audio_source_id)
    return


@app.task(ignore_result=True)
def create_snippet(snippet_id: int):
    """
    Create a snippet file.
    """
    time.sleep(1)  # To let the main process save changes to database.
    try:
        snippet = Snippet.objects.get(pk=snippet_id)
    except Snippet.DoesNotExist:
        logger.error("Snippet %s doesn't exist.", snippet_id)
        return
    if snippet.muted:
        logger.info("Muted snippets don't create new files.")
        return
    logger.info("Creating a file for snippet %s.", snippet_id)
    if snippet.file:
        filename = pathlib.Path(snippet.file).name
        match = re.match('^(\d+)_(\d+)\.mp3$', filename)
        beginning = int(match.group(1))
        length = int(match.group(2))
        if snippet.beginning == beginning and snippet.length == length and pathlib.Path(snippet.file).exists():
            logger.info("Snippet %s has already an OK file.", snippet_id)
            return

    # Recreate a snippet that's matching parameters.
    if snippet.file:
        os.unlink(snippet.file)
        snippet.file = ''
        snippet.save()

    new_name = "{}_{}.mp3".format(snippet.beginning, snippet.length)
    new_path = pathlib.Path(settings.MEDIA_ROOT, 'snippets', str(snippet.source_id), new_name)
    new_dir = new_path.parent
    new_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["ffmpeg", "-y", "-ss", str(snippet.beginning), "-i", str(snippet.source.file.path),
                    "-t", str(snippet.length), str(new_path)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    snippet.file = str(new_path.relative_to(settings.BASE_DIR))
    snippet.save()
    logger.info("Snippet {} file created.".format(snippet_id))
    return


@app.task(ignore_result=True)
def mute_snippet(snippet_id: int):
    """
    Apply muting over the piece of file specified by the snippet.
    """
    time.sleep(1)  # To let the main process save changes to database.
    try:
        snippet = Snippet.objects.get(pk=snippet_id)
    except Snippet.DoesNotExist:
        logger.error("Snippet %s doesn't exist.", snippet_id)
        return

    if not snippet.muted:
        logger.info("Snippet %s is not a muted snippet.", snippet_id)
        return

    file_path = pathlib.Path(snippet.source.transcoded_file.path).resolve()

    if snippet.source.status not in (AudioSource.STORED_IN_CLOUD, AudioSource.READY):
        logger.warning("Can't mute an audio source that is not transcoded.")
        return

    assert (file_path.is_file())

    new_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)

    logger.info("Muting range %d - %d of %s", snippet.beginning, snippet.ending, file_path)
    subprocess.run([
        'ffmpeg', '-y', '-i', str(file_path), '-af',
        "volume=enable='between(t,{},{})':volume=0".format(snippet.beginning, snippet.ending),
        new_file.name
    ])

    os.chmod(new_file.name, 0o644)
    shutil.move(new_file.name, str(file_path))
    if snippet.file:
        os.unlink(os.path.join(settings.BASE_DIR, snippet.file))
        snippet.file = None
        snippet.save()
    logger.info("File %s got muted in %d - %d", file_path, snippet.beginning, snippet.ending)
    return


@app.task(ignore_result=True)
def backup_palanaeum():
    """
    Create a ZIP package containing result of dumpdata command and the `media` folder.
    """
    # TODO lock the site while the backup is running
    logger.info("Starting backup process.")
    with tempfile.TemporaryDirectory() as d:
        dump_path = os.path.join(d, 'dump.json')
        logger.info("Starting data dump...")
        management.call_command('dumpdata', natural_foreign=True, output=dump_path)
        logger.info("Data dumped.")
        logger.info("Copying MEDIA_ROOT to %s...", os.path.join(d, 'media'))
        shutil.copytree(settings.MEDIA_ROOT, os.path.join(d, 'media'))
        logger.info('Copy done.')
        backup_path = os.path.join(settings.BACKUP_DIR, datetime.date.today().strftime("%Y-%m-%d.zip"))
        with zipfile.ZipFile(backup_path, mode='w') as backup_zip:
            for root, dirs, files in os.walk(d):
                for file in files:
                    filepath = os.path.join(root, file)
                    logger.info("Compressing {}...".format(filepath))
                    backup_zip.write(filepath,
                                     arcname=os.path.relpath(filepath, d))
            logger.info("{} created.".format(backup_path))


@app.task(ignore_result=True)
def upload_new_sources_to_cloud():
    """
    Looks for new audio sources that are already transcoded and sends them to cloud.
    Could also delete their original file from local drive, depending on configuration.
    """
    cloud = get_cloud_backend()

    if cloud is None:
        return

    sources_to_upload = AudioSource.objects.filter(status=AudioSource.READY, is_approved=True)

    for source in sources_to_upload:
        try:
            logger.info("Uploading source %s to cloud.", source)
            cloud.upload_source(source)
            logger.info("Uploading source %s finished.", source)
            if not get_config('audio_keep_original_file'):
                os.unlink(source.raw_file.path)
                logger.info("File %s deleted.", source.raw_file.path)
        except PalanaeumCloudError:
            logger.exception("An error occurred while uploading source %s", source)
