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
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'reversion',
    'sitetree',
    'ralph.accounts',
    'ralph.assets',
    'ralph.attachments',
    'ralph.back_office',
    'ralph.data_center',
    'ralph.licences',
    'ralph.supports',
    'ralph.lib.foundation',
    'ralph.lib.table',
    'ralph.data_importer',
    'ralph.dc_view',
    'ralph.reports',
    'ralph.lib.transitions',
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
URLCONF_MODULES = [ROOT_URLCONF]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'ralph.lib.template.loaders.AppTemplateLoader',
            ]
        },
    },
]

WSGI_APPLICATION = 'ralph.wsgi.application'

MYSQL_OPTIONS = {
    'sql_mode': 'TRADITIONAL',
    'charset': 'utf8',
    'init_command': """
    SET storage_engine=INNODB;
    SET character_set_connection=utf8,collation_connection=utf8_unicode_ci;
    SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
    """
}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_ENV_MYSQL_DATABASE', 'ralph_ng'),
        'USER': os.environ.get('DB_ENV_MYSQL_USER', 'ralph_ng'),
        'PASSWORD': os.environ.get('DB_ENV_MYSQL_PASSWORD', 'ralph_ng'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'OPTIONS': MYSQL_OPTIONS,
        'ATOMIC_REQUESTS': True,
    }
}

AUTH_USER_MODEL = 'accounts.RalphUser'

LANGUAGE_CODE = 'en-us'
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = os.path.join(BASE_DIR, 'var', 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'var', 'media')

# adapt message's tags to bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.ERROR: 'danger',
}

DEFAULT_DEPRECIATION_RATE = 25
CHECK_IP_HOSTNAME_ON_SAVE = True
ASSET_HOSTNAME_TEMPLATE = {
    'prefix': '{{ country_code|upper }}{{ code|upper }}',
    'postfix': '',
    'counter_length': 5,
}
DEFAULT_COUNTRY_CODE = 'POL'


LDAP_SERVER_OBJECT_USER_CLASS = 'user'  # possible values: user, person

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
        'ralph.data_importer': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'ralph.api.permissions.RalphPermission',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'ralph.lib.permissions.api.PermissionsForObjectFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',  # noqa
    'PAGE_SIZE': 10,
}
