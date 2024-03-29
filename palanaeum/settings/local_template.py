# Decide if you want to run in debug mode or not.
# Never use DEBUG mode in production!
DEBUG = False

# Set a very secret secret key!
SECRET_KEY = ''

# List your administrators
# https://docs.djangoproject.com/en/1.10/ref/settings/#admins
ADMINS = ()

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'PORT': '5432',
        'NAME': 'palanaeum',
        'USER': 'vagrant',
    }
}

# Set the communication gateway for Celery
# Redis is the easiest to use.
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# Configure e-mail backend
# Find more e-mail settings here:
# https://docs.djangoproject.com/en/1.10/ref/settings/#email
DEFAULT_FROM_EMAIL = 'no-reply@palanaeum.db'
SERVER_EMAIL = 'root@palanaeum'  # Error messages come from this address
EMAIL_SUBJECT_PREFIX = '[Palanaeum]'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Set a proper cache backend
# https://docs.djangoproject.com/en/1.10/ref/settings/#caches
# I suggest using Redis with django-redis-cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        # 'BACKEND': 'redis_cache.RedisCache',
        # 'LOCATION': '/var/run/redis/redis.sock',
        # 'OPTIONS': {
        #     'DB': 1,
        #     'PASSWORD': 'yadayada',
        #     'PARSER_CLASS': 'redis.connection.HiredisParser',
        #     'PICKLE_VERSION': 2,
        # },
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

# Pick one: 'blue' or 'green'
PALANAEUM_STYLE = 'blue'
