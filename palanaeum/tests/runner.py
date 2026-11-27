import shutil
import tempfile
import unittest
from pathlib import Path

from django.conf import settings
from django.core.cache import caches
from django.core.signals import setting_changed
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.functional import empty


def _reset_thread_locals():
    from palanaeum import middleware

    middleware._GLOBAL_REQUEST_BOX.request = None
    timezone.deactivate()


def rebind_module_caches():
    import palanaeum.configuration as configuration_mod
    import palanaeum.search as search_mod

    configuration_mod.cache = caches["config"]
    search_mod.SEARCH_CACHE = caches["search"]


def _reset_sorl_lazy_objects():
    from sorl.thumbnail import default as sorl_default

    sorl_default.kvstore._wrapped = empty
    sorl_default.storage._wrapped = empty


def _on_setting_changed(sender, setting, **kwargs):
    if setting == "CACHES":
        rebind_module_caches()
    elif setting in ("THUMBNAIL_KVSTORE", "MEDIA_ROOT"):
        _reset_sorl_lazy_objects()


class _ThreadLocalCleanupMixin:
    def startTest(self, test):
        _reset_thread_locals()
        super().startTest(test)

    def stopTest(self, test):
        try:
            super().stopTest(test)
        finally:
            _reset_thread_locals()


class PalanaeumTestRunner(DiscoverRunner):
    """
    Hermetic test runner that isolates filesystem paths, caches, sorl-thumbnail
    KV store, Celery broker, password hashers, and thread-local request/timezone
    state from local development services.
    """

    def get_resultclass(self):
        base_cls = super().get_resultclass() or unittest.TextTestResult
        return type(
            f"Palanaeum{base_cls.__name__}",
            (_ThreadLocalCleanupMixin, base_cls),
            {},
        )

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._temp_dir = Path(tempfile.mkdtemp(prefix="palanaeum_test_"))
        media_root = self._temp_dir / "media"
        config_uploads = media_root / "config"
        upload_dir = self._temp_dir / "uploads" / "done"
        chunks_dir = self._temp_dir / "uploads" / "chunks"
        backup_dir = self._temp_dir / "backups"
        for path in (media_root, config_uploads, upload_dir, chunks_dir, backup_dir):
            path.mkdir(parents=True, exist_ok=True)

        setting_changed.connect(
            _on_setting_changed,
            dispatch_uid="palanaeum.tests.runner.on_setting_changed",
        )

        self._override_cm = override_settings(
            MEDIA_ROOT=media_root,
            CONFIG_UPLOADS=config_uploads,
            UPLOAD_DIRECTORY=f"{upload_dir}/",
            CHUNKS_DIRECTORY=f"{chunks_dir}/",
            BACKUP_DIR=backup_dir,
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
                "search": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
                "config": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
            },
            THUMBNAIL_KVSTORE="sorl.thumbnail.kvstores.cached_db_kvstore.KVStore",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
        self._override_cm.__enter__()
        rebind_module_caches()
        _reset_sorl_lazy_objects()

        from palanaeum.celery import app as celery_app

        self._prev_celery_broker = celery_app.conf.broker_url
        self._prev_celery_backend = celery_app.conf.result_backend
        celery_app.conf.update(
            broker_url="memory://",
            result_backend="cache+memory://",
        )

    def teardown_test_environment(self, **kwargs):
        _reset_thread_locals()
        try:
            from palanaeum.celery import app as celery_app

            if hasattr(self, "_prev_celery_broker"):
                celery_app.conf.update(
                    broker_url=self._prev_celery_broker,
                    result_backend=self._prev_celery_backend,
                )
        finally:
            if hasattr(self, "_override_cm") and self._override_cm is not None:
                self._override_cm.__exit__(None, None, None)
                self._override_cm = None
            if hasattr(self, "_temp_dir") and self._temp_dir is not None:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
                self._temp_dir = None
            super().teardown_test_environment(**kwargs)
