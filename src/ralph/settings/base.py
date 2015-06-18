# -*- coding: utf-8 -*-
import os

from django.contrib.messages import constants as messages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'CHANGE_ME'

DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'ralph.admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'reversion',
    'sitetree',
    'ralph.accounts',
    'ralph.assets',
    'ralph.back_office',
    'ralph.data_center',
    'ralph.licences',
    'ralph.supports',
    'ralph.lib.foundation',
    'ralph.data_importer',
    'ralph.dc_view',
    'rest_framework',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'ralph.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ralph.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_ENV_MYSQL_DATABASE', 'ralph_ng'),
        'USER': os.environ.get('DB_ENV_MYSQL_USER', 'ralph_ng'),
        'PASSWORD': os.environ.get('DB_ENV_MYSQL_PASSWORD', 'ralph_ng'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'OPTIONS': {
            "init_command": ','.join([
                "SET storage_engine=INNODB",
                "character_set_connection=utf8",
                ";".join([
                    "collation_connection=utf8_unicode_ci",
                    "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED",
                    "",
                ])
            ])
        }
    }
}

AUTH_USER_MODEL = 'accounts.RalphUser'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# adapt message's tags to bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.ERROR: 'danger',
}

DEFAULT_DEPRECATION_RATE = 25
ASSET_HOSTNAME_TEMPLATE = 'test'

ADMIN_SITE_HEADER = 'Ralph 3'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'ralph.data_importer.management.commands.importer': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
