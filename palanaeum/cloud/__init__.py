import abc
import importlib
import os

from palanaeum.cloud.exceptions import InvalidSourceError
from palanaeum.configuration import get_config
from palanaeum.models import AudioSource

CLOUD_BACKENDS = {
    'none': None,
    'b2': 'palanaeum.cloud.b2.B2'
}

MAX_PART_FILE_SIZE = 20*1024*1024  # 20 Mb per part, to not clog memory


class CloudBackend(abc.ABC):
    """
    An abstract class defining interface required by Palanaeum
    to use a cloud backend to store files.
    """
    def __init__(self, cloud_login, cloud_passwd):
        self.cloud_login = cloud_login
        self.cloud_passwd = cloud_passwd

    @abc.abstractclassmethod
    def test_configuration(cls):
        """
        Test if the configuration stored in database is correct.
        Raise ConfigurationError if it's not.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_file_info(self, audio_source: AudioSource):
        """
        Returns data about the file stored in the cloud.
        """
        raise NotImplementedError

    def upload_source(self, audio_source: AudioSource, **kwargs):
        """
        Upload specified source to the cloud.
        Update the source metadata field with associated information.
        """
        if not os.path.isfile(audio_source.raw_file.path):
            raise FileNotFoundError

        if audio_source.status == AudioSource.STORED_IN_CLOUD:
            return

        if audio_source.status != AudioSource.READY:
            raise InvalidSourceError

        file_path = audio_source.raw_file.path

        headers = {
            'Event-Id': str(audio_source.event_id),
            'Event-Name': audio_source.event.name,
            'Title': audio_source.title,
        }

        audio_source.cloud_status = self.upload_file(file_path, headers, audio_source.raw_file.name)
        audio_source.status = AudioSource.STORED_IN_CLOUD
        audio_source.save()
        return

    def download_source(self, audio_source: AudioSource, **kwargs):
        """
        Download given audio source original file using information from metadata
        field.
        """
        self.download_file(audio_source.raw_file.name, audio_source.raw_file.path)

    @abc.abstractmethod
    def upload_file(self, file_path, extra_params=None, file_name=""):
        """
        Use this function to store a file in the cloud.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def download_file(self, file_name, dest_path: str):
        """
        Download a file by it's name.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_download_url(self, audio_source: AudioSource):
        """
        Return an URL that will allow anyone to download the original file.
        The URL may expire after some time.
        """
        raise NotImplementedError


def get_cloud_backend() -> CloudBackend:
    """
    Returns an instance of CloudBackend subclass configured and ready for action.
    If there is no cloud backend configured, None is returned.
    """
    backend_name = get_config('cloud_backend')
    if CLOUD_BACKENDS[backend_name] is None:
        return None
    package, class_name = CLOUD_BACKENDS[backend_name].rsplit('.', maxsplit=1)
    backend_class = getattr(importlib.import_module(package), class_name)
    assert(issubclass(backend_class, CloudBackend))
    cloud_login = get_config('cloud_login')
    cloud_passwd = get_config('cloud_passwd')
    return backend_class(cloud_login, cloud_passwd)