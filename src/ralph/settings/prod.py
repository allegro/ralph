from ralph.settings import *  # noqa

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'  # noqa
STATIC_ROOT = os.path.join(BASE_DIR, 'var', 'static')

# FIXME: when going for full production, change it to False

DEBUG = True

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.TokenAuthentication',
    # session authentication enabled for API requests from UI (ex. in
    # visualisation)
    'rest_framework.authentication.SessionAuthentication',
)
