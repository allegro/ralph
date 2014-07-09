#
# A testing profile.
#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {},
    }
}

PLUGGABLE_APPS = ['assets']

SOUTH_TESTS_MIGRATE = False

ASSETS_AUTO_ASSIGN_HOSTNAME = True
