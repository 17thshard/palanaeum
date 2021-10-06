"""
Django settings for Palanaeum project.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

RUNSERVERPLUS_SERVER_ADDRESS_PORT = '127.0.0.1:9000'

PALANAEUM_VERSION = '1.1.0'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.postgres',
    'django_extensions',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'debug_toolbar',
    'sorl.thumbnail',
    'raven.contrib.django.raven_compat',
    'palanaeum.apps.PalanaeumConfig'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'palanaeum.middleware.TimezoneMiddleware',
    'palanaeum.middleware.GlobalRequestKeeper'
]

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

ROOT_URLCONF = 'palanaeum.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'palanaeum.context_processors.palanaeum_context'
            ],
        },
    },
]

WSGI_APPLICATION = 'palanaeum.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'NAME': 'palanaeum',
        'USER': 'vagrant',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STATIC_URL = '/collected-statics/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected-statics')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'compressor.finders.CompressorFinder',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
CONFIG_UPLOADS = os.path.join(MEDIA_ROOT, 'config')

# Celery conf
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_CELERYD_TASK_TIME_LIMIT = 60*60
CELERY_BEAT_SCHEDULE = {
    'upload_audio_sources_to_cloud': {
        'task': 'palanaeum.tasks.upload_new_sources_to_cloud',
        'schedule': timedelta(hours=1)
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'search': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'config': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

TINYMCE_API_KEY = ''

THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_UPSCALE = False
THUMBNAIL_PRESERVE_FORMAT = True


BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
try:
    os.mkdir(BACKUP_DIR)
except FileExistsError:
    pass

LOGIN_REDIRECT_URL = '/'

# Fine Uploader settings
UPLOAD_DIRECTORY = '/tmp/palanaeum_uploads/done/'
CHUNKS_DIRECTORY = '/tmp/palanaeum_uploads/chunks/'
UPLOAD_FILE_SIZE_LIMIT = 500 * 1024 * 1024  # In bytes
UPLOAD_IMAGE_FILE_SIZE_LIMIT = 5 * 1024 * 1024  # In bytes


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'django_log_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose'
        },
        'palanaeum_log_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'palanaeum.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['django_log_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'palanaeum': {
            'handlers': ['palanaeum_log_file', 'mail_admins', 'console'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/min',
    }
}

CORS_ORIGIN_ALLOW_ALL = True
