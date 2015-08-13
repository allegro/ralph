from ralph.settings import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ('django_plainpasswordhasher.PlainPasswordHasher', )

INSTALLED_APPS += (
    'ralph.lib.mixins',
    'ralph.tests',
    'ralph.lib.permissions.tests',
)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

ROOT_URLCONF = 'ralph.urls.base'
