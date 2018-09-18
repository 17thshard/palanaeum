import logging
import os
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import ProgrammingError
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.cache import caches

cache = caches['config']
logger = logging.getLogger('palanaeum.admin')

CONFIG_ENTRIES = {
    # key: (type, default value)
    'page_title': ('str', 'Palanaeum'),
    'default_page_length': ('int', 20),
    'approval_message': ('str', 'Reviewed'),
    'review_pending_explanation': ('str', 'This event is waiting for review. The information here might not be correct.'),
    'review_reviewed_explanation': ('str', 'This event has been reviewed. Information presented here is correct.'),
    'index_hello': ('str', 'Welcome to Palanaeum, the free transcription and archiving platform!'),
    'google_analytics': ('str', ''),
    'audio_keep_original_file': ('bool', True),
    'audio_quality': ('str', '128k'),
    'cloud_backend': ('str', ''),
    'cloud_login': ('str', ''),
    'cloud_passwd': ('str', ''),
    'cloud_b2_bucket_id': ('str', ''),
    'audio_staff_size_limit': ('int', 1000),
    'audio_user_size_limit': ('int', 100),
    'image_size_limit': ('int', 10),
    'logo_file': ('file', ''),
    'favicon16': ('file', ''),
    'favicon32': ('file', ''),
    'favicon96': ('file', ''),
    'favicon120': ('file', ''),
    'favicon152': ('file', ''),
    'favicon167': ('file', ''),
    'favicon180': ('file', ''),
}


@receiver(post_migrate)
def config_update(*args, **kwargs):
    from palanaeum.models import ConfigEntry
    for key, val in CONFIG_ENTRIES.items():
        ConfigEntry.objects.get_or_create(key=key, defaults={'value': _serialize_value(key, val[1])})


def _deserialize_value(key, value):
    value_type = CONFIG_ENTRIES[key][0]

    if value_type == 'str':
        return str(value)
    elif value_type == 'int':
        return int(value)
    elif value_type == 'bool':
        return value == '1'
    elif value_type == 'file':
        return urljoin(settings.MEDIA_URL, value) if value else None
    else:
        raise NotImplementedError


def _serialize_value(key, value):
    value_type = CONFIG_ENTRIES[key][0]

    if value_type in ('str', 'file', 'int'):
        return str(value)
    elif value_type == 'bool':
        return '1' if value else '0'
    else:
        raise NotImplementedError


def get_config(key: str):
    from palanaeum.models import ConfigEntry
    value = cache.get(key)

    if value is not None:
        return _deserialize_value(key, value)

    try:
        value = ConfigEntry.objects.get(key=key).value
        cache.set(key, value)
    except ConfigEntry.DoesNotExist:
        value = CONFIG_ENTRIES[key][1]
    except ProgrammingError:
        logger.exception("Can't get config entry for %s.", key)
        return None

    return _deserialize_value(key, value)


def set_config(key: str, value):
    from palanaeum.models import ConfigEntry
    value = _serialize_value(key, value)
    ConfigEntry.objects.update_or_create(key=key, defaults={'value': value})
    cache.set(key, value)
    return value


def set_config_file(key: str, file: UploadedFile):
    from palanaeum.models import ConfigEntry

    try:
        entry = ConfigEntry.objects.get(key=key)
        if entry.value:
            os.unlink(os.path.join(settings.MEDIA_ROOT, entry.value))
    except ConfigEntry.DoesNotExist:
        entry = ConfigEntry(key=key)
    except FileNotFoundError:
        pass

    file_path = os.path.join(settings.CONFIG_UPLOADS, file.name)
    os.makedirs(settings.CONFIG_UPLOADS, exist_ok=True)
    entry.value = os.path.relpath(file_path, settings.MEDIA_ROOT)

    with open(file_path, mode='wb') as write_file:
        for chunk in file.chunks():
            write_file.write(chunk)

    entry.save()
    cache.set(key, entry.value)
    return


def get_config_dict():
    from palanaeum.models import ConfigEntry
    return {
        entry.key: _deserialize_value(entry.key, entry.value)
        for entry in ConfigEntry.objects.all()
    }
