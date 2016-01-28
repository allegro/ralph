import json
import os

from ralph.settings import *  # noqa

# FIXME: when going for full production, change it to False
DEBUG = False

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'  # noqa

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.TokenAuthentication',
    # session authentication enabled for API requests from UI (ex. in
    # visualisation)
    'rest_framework.authentication.SessionAuthentication',
)

if os.environ.get('STORE_SESSIONS_IN_REDIS'):
    SESSION_ENGINE = 'redis_sessions.session'
    SESSION_REDIS_HOST = REDIS_CONNECTION['HOST']
    SESSION_REDIS_PORT = REDIS_CONNECTION['PORT']
    SESSION_REDIS_DB = REDIS_CONNECTION['DB']
    SESSION_REDIS_PASSWORD = REDIS_CONNECTION['PASSWORD']
    SESSION_REDIS_PREFIX = 'session'

if os.environ.get('USE_REDIS_CACHE'):
    DEFAULT_CACHE_OPTIONS = {
        'DB': os.environ.get('REDIS_CACHE_DB', REDIS_CONNECTION['DB']),
        'PASSWORD': os.environ.get(
            'REDIS_CACHE_PASSWORD', REDIS_CONNECTION['PASSWORD']
        ),
        'PARSER_CLASS': os.environ.get(
            'REDIS_CACHE_PARSER', 'redis.connection.HiredisParser'
        ),
        'CONNECTION_POOL_CLASS': os.environ.get(
            'REDIS_CACHE_CONNECTION_POOL_CLASS',
            'redis.BlockingConnectionPool'
        ),
        'PICKLE_VERSION': -1,
    }
    CACHES = {
        'default': {
            'BACKEND': os.environ.get(
                'REDIS_CACHE_BACKEND', 'redis_cache.RedisCache'
            ),
            'LOCATION': json.loads(
                os.environ.get('REDIS_CACHE_LOCATION', '"{}:{}"'.format(
                    REDIS_CONNECTION['HOST'], REDIS_CONNECTION['PORT']
                ))
            ),
            'OPTIONS': (
                json.loads(os.environ.get('REDIS_CACHE_OPTIONS', "{}")) or
                DEFAULT_CACHE_OPTIONS
            ),
        },
    }
