from ralph.settings import *  # noqa

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'  # noqa
STATIC_ROOT = os.path.join(BASE_DIR, 'var', 'static')

LDAP_SERVER_OBJECT_USER_CLASS = 'user'  # possible values: "user, person
