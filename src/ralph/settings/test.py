from ralph.settings import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


INSTALLED_APPS += (
    'ralph.lib',
)
