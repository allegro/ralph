from ralph.settings import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
    }
}

PASSWORD_HASHERS = ('django_plainpasswordhasher.PlainPasswordHasher', )

INSTALLED_APPS += (
    'ralph.lib.mixins',
    'ralph.tests',
    'ralph.lib.permissions.tests',
    'ralph.lib.polymorphic.tests',
)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

ROOT_URLCONF = 'ralph.urls.test'
# specify all url modules to reload during specific tests
# see `ralph.tests.mixins.ReloadUrlsMixin` for details
URLCONF_MODULES = ['ralph.urls.base', ROOT_URLCONF]
