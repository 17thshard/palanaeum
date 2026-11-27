import os
import random
import subprocess

from django.apps import AppConfig
from django.conf import settings

_HEX_CHARS = "0123456789abcdef"


class PalanaeumConfig(AppConfig):
    name = 'palanaeum'

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.version = "?"

    def ready(self):
        version_tag = os.getenv("PALA_VERSION_TAG", "").strip()
        if version_tag:
            self.version = version_tag
            return

        try:
            self.version = subprocess.check_output(
                ['git', 'rev-parse', '--verify', 'HEAD', '--short'],
                cwd=settings.BASE_DIR,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            # No git installed or we're not a git instance at all
            # We generate a random version tag
            self.version = 'r' + "".join(random.sample(_HEX_CHARS, 6))
