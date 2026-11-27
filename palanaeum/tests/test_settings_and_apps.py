import io
import os
import runpy
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIHandler
from django.test import SimpleTestCase

import palanaeum
from palanaeum import celery as palanaeum_celery
from palanaeum import wsgi as palanaeum_wsgi
from palanaeum.apps import PalanaeumConfig


class SettingsTests(SimpleTestCase):
    SETTINGS_PATH = Path(settings.BASE_DIR) / "palanaeum" / "settings.py"

    def _run_settings(self, env_vars=None, env_file_text=""):
        with tempfile.TemporaryDirectory(prefix="palanaeum_settings_test_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            env_file = tmp_path / ".env"
            env_file.write_text(env_file_text, encoding="utf-8")

            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "PALA_ENV_FILE": str(env_file),
                "PALA_BACKUP_DIR": str(tmp_path / "backups"),
                "PALA_MEDIA_ROOT": str(tmp_path / "media"),
                "PALA_UPLOAD_DIRECTORY": str(tmp_path / "uploads" / "done") + "/",
                "PALA_CHUNKS_DIRECTORY": str(tmp_path / "uploads" / "chunks") + "/",
            }
            if env_vars:
                clean_env.update(env_vars)

            with mock.patch.dict(os.environ, clean_env, clear=True):
                return runpy.run_path(str(self.SETTINGS_PATH))

    def test_debug_false_without_secret_key_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            self._run_settings({"PALA_DEBUG": "False"})

    def test_debug_true_without_secret_key_uses_fallback_and_debug_toolbar(self):
        ns = self._run_settings({"PALA_DEBUG": "True"})
        self.assertTrue(ns["DEBUG"])
        self.assertEqual(ns["SECRET_KEY"], "dev-insecure-secret-key")
        self.assertEqual(ns["ALLOWED_HOSTS"], ["localhost", "127.0.0.1"])
        self.assertIn("debug_toolbar", ns["INSTALLED_APPS"])
        self.assertIn(
            "debug_toolbar.middleware.DebugToolbarMiddleware",
            ns["MIDDLEWARE"],
        )
        self.assertEqual(ns["INTERNAL_IPS"], ["127.0.0.1"])

    def test_debug_false_with_secret_key_omits_debug_toolbar_and_default_hosts(self):
        ns = self._run_settings({
            "PALA_DEBUG": "False",
            "PALA_SECRET_KEY": "prod-secret-key",
        })
        self.assertFalse(ns["DEBUG"])
        self.assertEqual(ns["SECRET_KEY"], "prod-secret-key")
        self.assertEqual(ns["ALLOWED_HOSTS"], [])
        self.assertNotIn("debug_toolbar", ns["INSTALLED_APPS"])
        self.assertNotIn(
            "debug_toolbar.middleware.DebugToolbarMiddleware",
            ns["MIDDLEWARE"],
        )

    def test_pala_style_validation(self):
        for style in ("blue", "green", "pink"):
            ns = self._run_settings({"PALA_DEBUG": "True", "PALA_STYLE": style})
            self.assertEqual(ns["PALANAEUM_STYLE"], style)

        with self.assertRaises(ImproperlyConfigured):
            self._run_settings({"PALA_DEBUG": "True", "PALA_STYLE": "purple"})

    def test_pala_cache_config_validation(self):
        ns_dummy = self._run_settings({
            "PALA_DEBUG": "True",
            "PALA_CACHE_CONFIG": "dummy",
        })
        for alias in ("default", "search", "config"):
            self.assertEqual(
                ns_dummy["CACHES"][alias]["BACKEND"],
                "django.core.cache.backends.dummy.DummyCache",
            )

        ns_redis = self._run_settings({
            "PALA_DEBUG": "True",
            "PALA_CACHE_CONFIG": "REDIS",
            "PALA_REDIS_HOST": "redis.internal",
            "PALA_REDIS_PORT": "6380",
            "PALA_REDIS_DB": "3",
        })
        for alias in ("default", "search", "config"):
            self.assertEqual(
                ns_redis["CACHES"][alias]["BACKEND"],
                "django.core.cache.backends.redis.RedisCache",
            )
            self.assertEqual(
                ns_redis["CACHES"][alias]["LOCATION"],
                "redis://redis.internal:6380",
            )
        self.assertEqual(ns_redis["CELERY_BROKER_URL"], "redis://redis.internal:6380/3")
        self.assertEqual(ns_redis["CELERY_RESULT_BACKEND"], "redis://redis.internal:6380/3")

        with self.assertRaises(ImproperlyConfigured):
            self._run_settings({
                "PALA_DEBUG": "True",
                "PALA_CACHE_CONFIG": "memcached",
            })

    def test_env_list_parses_and_strips_whitespace(self):
        ns = self._run_settings({
            "PALA_DEBUG": "True",
            "PALA_ALLOWED_HOSTS": " example.com , , sub.example.com , ",
            "PALA_CSRF_TRUSTED_ORIGINS": " https://a.test , https://b.test ",
            "PALA_ADMINS": " ops@test.com , admin@test.com ",
            "PALA_INTERNAL_IPS": " 10.0.0.1 , 10.0.0.2 ",
        })
        self.assertEqual(ns["ALLOWED_HOSTS"], ["example.com", "sub.example.com"])
        self.assertEqual(
            ns["CSRF_TRUSTED_ORIGINS"],
            ["https://a.test", "https://b.test"],
        )
        self.assertEqual(ns["ADMINS"], ["ops@test.com", "admin@test.com"])
        self.assertEqual(ns["INTERNAL_IPS"], ["10.0.0.1", "10.0.0.2"])

    def test_email_backend_defaults_and_override(self):
        ns_console = self._run_settings({"PALA_DEBUG": "True"})
        self.assertIsNone(ns_console["EMAIL_HOST"])
        self.assertEqual(
            ns_console["EMAIL_BACKEND"],
            "django.core.mail.backends.console.EmailBackend",
        )

        ns_smtp = self._run_settings({
            "PALA_DEBUG": "True",
            "PALA_EMAIL_HOST": "smtp.example.com",
        })
        self.assertEqual(ns_smtp["EMAIL_HOST"], "smtp.example.com")
        self.assertEqual(
            ns_smtp["EMAIL_BACKEND"],
            "django.core.mail.backends.smtp.EmailBackend",
        )

        ns_explicit = self._run_settings({
            "PALA_DEBUG": "True",
            "PALA_EMAIL_HOST": "smtp.example.com",
            "PALA_EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        })
        self.assertEqual(
            ns_explicit["EMAIL_BACKEND"],
            "django.core.mail.backends.locmem.EmailBackend",
        )

    def test_proxy_ssl_header_and_secure_cookies_and_upload_permissions(self):
        ns_default = self._run_settings({"PALA_DEBUG": "True"})
        self.assertEqual(
            ns_default["SECURE_PROXY_SSL_HEADER"],
            ("HTTP_X_FORWARDED_PROTO", "https"),
        )
        self.assertFalse(ns_default["SESSION_COOKIE_SECURE"])
        self.assertFalse(ns_default["CSRF_COOKIE_SECURE"])
        self.assertEqual(ns_default["FILE_UPLOAD_PERMISSIONS"], 0o644)
        self.assertEqual(ns_default["FILE_UPLOAD_DIRECTORY_PERMISSIONS"], 0o755)

        ns_custom = self._run_settings({
            "PALA_DEBUG": "False",
            "PALA_SECRET_KEY": "prod-secret-key",
            "PALA_USE_X_FORWARDED_PROTO": "False",
            "PALA_SECURE_COOKIES": "True",
        })
        self.assertNotIn("SECURE_PROXY_SSL_HEADER", ns_custom)
        self.assertTrue(ns_custom["SESSION_COOKIE_SECURE"])
        self.assertTrue(ns_custom["CSRF_COOKIE_SECURE"])

    def test_reads_pala_env_file(self):
        ns = self._run_settings(
            env_file_text=(
                "PALA_DEBUG=False\n"
                "PALA_SECRET_KEY=from-env-file\n"
                "PALA_STYLE=pink\n"
                "PALA_SITE_ID=7\n"
                "PALA_CORS_ALLOW_ALL=False\n"
            )
        )
        self.assertFalse(ns["DEBUG"])
        self.assertEqual(ns["SECRET_KEY"], "from-env-file")
        self.assertEqual(ns["PALANAEUM_STYLE"], "pink")
        self.assertEqual(ns["SITE_ID"], 7)
        self.assertFalse(ns["CORS_ALLOW_ALL_ORIGINS"])


class AppConfigCeleryWSGITests(SimpleTestCase):
    def test_app_config_ready_uses_env_version_tag_when_set(self):
        cfg = PalanaeumConfig("palanaeum", palanaeum)
        with mock.patch.dict(os.environ, {"PALA_VERSION_TAG": "v1.2.3"}):
            with mock.patch("palanaeum.apps.subprocess.check_output") as mock_git:
                cfg.ready()
        self.assertEqual(cfg.version, "v1.2.3")
        mock_git.assert_not_called()

    def test_app_config_ready_git_success(self):
        cfg = PalanaeumConfig("palanaeum", palanaeum)
        self.assertEqual(cfg.version, "?")
        with mock.patch.dict(os.environ, {"PALA_VERSION_TAG": ""}):
            with mock.patch("palanaeum.apps.subprocess.check_output", return_value="deadbeef\n"):
                cfg.ready()
        self.assertEqual(cfg.version, "deadbeef")

    def test_app_config_ready_fallback_on_subprocess_error(self):
        for exc in (subprocess.CalledProcessError(1, ["git"]), FileNotFoundError("no git")):
            cfg = PalanaeumConfig("palanaeum", palanaeum)
            with mock.patch.dict(os.environ, {"PALA_VERSION_TAG": ""}):
                with mock.patch("palanaeum.apps.subprocess.check_output", side_effect=exc):
                    cfg.ready()
            self.assertTrue(cfg.version.startswith("r"))
            self.assertEqual(len(cfg.version), 7)
            int(cfg.version[1:], 16)

    def test_celery_app_and_debug_task(self):
        self.assertIs(palanaeum.celery_app, palanaeum_celery.app)
        self.assertEqual(palanaeum_celery.app.main, "palanaeum")
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            palanaeum_celery.debug_task.run()
        self.assertIn("Request:", buf.getvalue())

    def test_wsgi_application_is_callable_handler(self):
        self.assertIsInstance(palanaeum_wsgi.application, WSGIHandler)
        self.assertTrue(callable(palanaeum_wsgi.application))
