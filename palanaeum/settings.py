"""
Django settings for Palanaeum project.

Configuration is read from environment variables (and optionally a `.env` file
in the project root, or the path specified by `PALA_ENV_FILE`). All
project-specific environment variables use the `PALA_` prefix.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
_env_file = os.getenv("PALA_ENV_FILE")
if _env_file:
    environ.Env.read_env(_env_file)
elif (BASE_DIR / ".env").is_file():
    environ.Env.read_env(BASE_DIR / ".env")


def _env_list(var_name: str, default: list[str] | None = None) -> list[str]:
    values = env.list(var_name, default=default if default is not None else [])
    return [item.strip() for item in values if item.strip()]


# Core & Security

DEBUG = env.bool("PALA_DEBUG", default=False)

SECRET_KEY = env.str("PALA_SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-insecure-secret-key"
    else:
        raise ImproperlyConfigured(
            "PALA_SECRET_KEY must be set when PALA_DEBUG is False."
        )

ALLOWED_HOSTS = _env_list(
    "PALA_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"] if DEBUG else [],
)
CSRF_TRUSTED_ORIGINS = _env_list("PALA_CSRF_TRUSTED_ORIGINS", default=[])

RUNSERVERPLUS_SERVER_ADDRESS_PORT = env.str(
    "PALA_DEV_SERVER_ADDR", default="127.0.0.1:9000"
)

PALANAEUM_VERSION = "1.2.0"

PALANAEUM_STYLE = env.str("PALA_STYLE", default="blue")
if PALANAEUM_STYLE not in {"blue", "green", "pink"}:
    raise ImproperlyConfigured(
        f"Unknown PALA_STYLE: {PALANAEUM_STYLE!r}. Expected 'blue', 'green', or 'pink'."
    )


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.postgres",
    "django_extensions",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "sorl.thumbnail",
    "palanaeum.apps.PalanaeumConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "palanaeum.middleware.TimezoneMiddleware",
    "palanaeum.middleware.GlobalRequestKeeper",
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = _env_list("PALA_INTERNAL_IPS", default=["127.0.0.1"])

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

ROOT_URLCONF = "palanaeum.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "palanaeum.context_processors.palanaeum_context",
            ],
        },
    },
]

WSGI_APPLICATION = "palanaeum.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env.str("PALA_DB_HOST", default="127.0.0.1"),
        "PORT": env.str("PALA_DB_PORT", default="5432"),
        "NAME": env.str("PALA_DB_NAME", default="palanaeum"),
        "USER": env.str("PALA_DB_USER", default="palanaeum"),
        "PASSWORD": env.str("PALA_DB_PASSWORD", default="") or None,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization & Sites

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
SITE_ID = env.int("PALA_SITE_ID", default=1)


# Static files, Media, Backups & Uploads

STATIC_URL = "/collected-statics/"
STATIC_ROOT = BASE_DIR / "collected-statics"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

MEDIA_ROOT = Path(env.str("PALA_MEDIA_ROOT", default=str(BASE_DIR / "media")))
MEDIA_URL = "/media/"
CONFIG_UPLOADS = MEDIA_ROOT / "config"

BACKUP_DIR = Path(env.str("PALA_BACKUP_DIR", default=str(BASE_DIR / "backups")))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_REDIRECT_URL = "/"

# Fine Uploader settings
UPLOAD_DIRECTORY = env.str(
    "PALA_UPLOAD_DIRECTORY", default="/tmp/palanaeum_uploads/done/"
)
CHUNKS_DIRECTORY = env.str(
    "PALA_CHUNKS_DIRECTORY", default="/tmp/palanaeum_uploads/chunks/"
)
UPLOAD_FILE_SIZE_LIMIT = 500 * 1024 * 1024  # 500 MB
UPLOAD_IMAGE_FILE_SIZE_LIMIT = 5 * 1024 * 1024  # 5 MB


# Redis, Celery, Cache & Thumbnails

_REDIS_HOST = env.str("PALA_REDIS_HOST", default="127.0.0.1")
_REDIS_PORT = env.int("PALA_REDIS_PORT", default=6379)
_REDIS_DB = env.int("PALA_REDIS_DB", default=0)
_REDIS_BASE_URL = f"redis://{_REDIS_HOST}:{_REDIS_PORT}"

CELERY_BROKER_URL = f"{_REDIS_BASE_URL}/{_REDIS_DB}"
CELERY_RESULT_BACKEND = f"{_REDIS_BASE_URL}/{_REDIS_DB}"
CELERY_TASK_TIME_LIMIT = 60 * 60
CELERY_BEAT_SCHEDULE = {
    "upload_audio_sources_to_cloud": {
        "task": "palanaeum.tasks.upload_new_sources_to_cloud",
        "schedule": timedelta(hours=6),
    }
}

_CACHE_CONFIG = env.str("PALA_CACHE_CONFIG", default="dummy").lower()
if _CACHE_CONFIG == "dummy":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
        "search": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
        "config": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
    }
elif _CACHE_CONFIG == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _REDIS_BASE_URL,
        },
        "search": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _REDIS_BASE_URL,
        },
        "config": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _REDIS_BASE_URL,
        },
    }
else:
    raise ImproperlyConfigured(
        f"Unknown PALA_CACHE_CONFIG: {_CACHE_CONFIG!r}. Expected 'dummy' or 'redis'."
    )

THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.redis_kvstore.KVStore"
THUMBNAIL_REDIS_HOST = _REDIS_HOST
THUMBNAIL_REDIS_PORT = _REDIS_PORT
THUMBNAIL_UPSCALE = False
THUMBNAIL_PRESERVE_FORMAT = True

TINYMCE_API_KEY = env.str("PALA_TINYMCE_API_KEY", default="")


# Logging

_DJANGO_LOG_LEVEL = env.str("PALA_DJANGO_LOG_LEVEL", default="INFO")
_APP_LOG_LEVEL = env.str("PALA_LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["mail_admins", "console"],
            "level": _DJANGO_LOG_LEVEL,
            "propagate": True,
        },
        "palanaeum": {
            "handlers": ["mail_admins", "console"],
            "level": _APP_LOG_LEVEL,
            "propagate": False,
        },
    },
}


# REST Framework & CORS

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "10/second",
    },
}

CORS_ALLOW_ALL_ORIGINS = env.bool("PALA_CORS_ALLOW_ALL", default=True)


# Admins & Email

# Comma-separated list of admin email addresses, e.g. admin@example.com,ops@example.com
ADMINS = _env_list("PALA_ADMINS", default=[])

EMAIL_HOST = env.str("PALA_EMAIL_HOST", default="") or None
EMAIL_BACKEND = env.str(
    "PALA_EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.smtp.EmailBackend"
        if EMAIL_HOST
        else "django.core.mail.backends.console.EmailBackend"
    ),
)
EMAIL_PORT = env.int("PALA_EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("PALA_EMAIL_USER", default="") or None
EMAIL_HOST_PASSWORD = env.str("PALA_EMAIL_PASSWORD", default="") or None
EMAIL_USE_TLS = env.bool("PALA_EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env.str("PALA_EMAIL_FROM", default="palanaeum@mestiv.dev")
SERVER_EMAIL = env.str("PALA_EMAIL_SERVER", default="pala-root@mestiv.dev")
EMAIL_SUBJECT_PREFIX = env.str("PALA_EMAIL_PREFIX", default="[Palanaeum]")
