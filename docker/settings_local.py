import os

# TEMPORARY (NOT FOR PRODUCTION USE RIGHT NOW)
from ralph.settings.dev import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_ENV_MYSQL_DATABASE', 'ralph_ng'),
        'USER': os.environ.get('DB_ENV_MYSQL_USER', 'ralph_ng'),
        'PASSWORD': os.environ.get('DB_ENV_MYSQL_PASSWORD', 'ralph_ng'),
        'HOST': os.environ.get('DB_HOST', 'db'),
    }
}
