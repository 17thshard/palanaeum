class PalanaeumCloudError(Exception):
    pass


class ConfigurationError(PalanaeumCloudError):
    pass


class AuthorizationError(PalanaeumCloudError):
    pass


class InvalidSourceError(PalanaeumCloudError):
    pass


class FileNotStored(PalanaeumCloudError):
    pass


class UploadFailed(PalanaeumCloudError):
    pass

class DownloadError(PalanaeumCloudError):
    pass