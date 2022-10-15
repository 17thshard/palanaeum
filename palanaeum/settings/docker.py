from .base import *

# Decide if you want to run in debug mode or not.
# Never use DEBUG mode in production!
DEBUG = True

# Set a very secret secret key!
SECRET_KEY = 'dhdfghdzxffyjhryr45345egh456yudtr'

# List your administrators
# https://docs.djangoproject.com/en/1.10/ref/settings/#admins
ADMINS = ()

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db',
        'PORT': '5432',
        'NAME': 'palanaeum',
        'USER': 'docker',
    }
}

# Set the communication gateway for Celery
# Redis is the easiest to use.
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

# Configure e-mail backend
# Find more e-mail settings here:
# https://docs.djangoproject.com/en/1.10/ref/settings/#email
DEFAULT_FROM_EMAIL = 'no-reply@palanaeum.db'
SERVER_EMAIL = 'root@palanaeum'  # Error messages come from this address
EMAIL_SUBJECT_PREFIX = '[Palanaeum]'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

THUMBNAIL_REDIS_HOST = 'redis'

# Set a proper cache backend
# https://docs.djangoproject.com/en/1.10/ref/settings/#caches
# I suggest using Redis with django-redis-cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    },
    'search': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'config': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# TinyMCE API Key:
TINYMCE_API_KEY = 'Put your key here'

RUNSERVERPLUS_SERVER_ADDRESS_PORT = '0.0.0.0:9000'
