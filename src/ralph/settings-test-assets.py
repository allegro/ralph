#
# A testing profile.
#
import os

if os.environ.get('TEST_DATABASE_ENGINE') == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'ralph',
            'USER': 'root',
            'HOST': 'localhost',
        },
    }
else:
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

PLUGGABLE_APPS = ['cmdb', 'assets']

SOUTH_TESTS_MIGRATE = False

ASSETS_AUTO_ASSIGN_HOSTNAME = True
