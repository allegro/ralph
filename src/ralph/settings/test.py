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
    'ralph.lib',
    'ralph.tests',
)

ROOT_URLCONF = 'ralph.urls.base'
