import random
import string
import subprocess

from django.apps import AppConfig
from django.conf import settings


class PalanaeumConfig(AppConfig):
    name = 'palanaeum'

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.version = "?"

    def ready(self):
        try:
            self.version = subprocess.check_output(
                ['git', 'rev-parse', '--verify', 'HEAD', '--short'],
                cwd=settings.BASE_DIR, universal_newlines=True
            ).strip()
            print(self.version, "THIS HAPPENS!!!!!")
        except (FileNotFoundError, subprocess.CalledProcessError):
            # No git installed or we're not a git instance at all
            # We generate a random version tag
            signs = set(string.hexdigits.lower())
            self.version = 'r' + "".join(random.sample(signs, 6))

