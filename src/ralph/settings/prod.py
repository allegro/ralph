import os

from ralph.settings import *  # noqa

# FIXME: when going for full production, change it to False
DEBUG = True
TEMPLATE_DEBUG = DEBUG

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
    SESSION_REDIS_PREFIX = 'session'
