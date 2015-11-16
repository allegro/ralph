# -*- coding: utf-8 -*-
import os

from django.contrib.messages import constants as messages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE_ME')

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
    'mptt',
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
    'ralph.lib.permissions',
    'rest_framework',
    'rest_framework.authtoken',
    'taggit',
    'taggit_serializer',
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
        'NAME': os.environ.get('DATABASE_NAME', 'ralph_ng'),
        'USER': os.environ.get('DATABASE_USER', 'ralph_ng'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'ralph_ng'),
        'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DATABASE_PORT', 3306),
        'OPTIONS': MYSQL_OPTIONS,
        'ATOMIC_REQUESTS': True,
    }
}

AUTH_USER_MODEL = 'accounts.RalphUser'
LOGIN_URL = '/login/'

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
STATIC_ROOT = os.environ.get(
    'STATIC_ROOT', os.path.join(BASE_DIR, 'var', 'static')
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get(
    'MEDIA_ROOT', os.path.join(BASE_DIR, 'var', 'media')
)

# adapt message's tags to bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.ERROR: 'danger',
}

DEFAULT_DEPRECIATION_RATE = int(os.environ.get('DEFAULT_DEPRECIATION_RATE', 25))
CHECK_IP_HOSTNAME_ON_SAVE = True
ASSET_HOSTNAME_TEMPLATE = {
    'prefix': '{{ country_code|upper }}{{ code|upper }}',
    'postfix': '',
    'counter_length': 5,
}
DEFAULT_COUNTRY_CODE = os.environ.get('DEFAULT_COUNTRY_CODE', 'POL')


LDAP_SERVER_OBJECT_USER_CLASS = 'user'  # possible values: user, person

ADMIN_SITE_HEADER = 'Ralph 3'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'datefmt': '%d.%m.%Y %H:%M:%S',
            'format': (
                '[%(asctime)08s,%(msecs)03d] %(levelname)-7s [%(processName)s'
                ' %(process)d] %(module)s - %(message)s'),
        },
        'simple': {
            'datefmt': '%H:%M:%S',
            'format': '[%(asctime)08s] %(levelname)-7s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
            'backupCount': 10,
            'filename': os.environ.get(
                'LOG_FILEPATH', os.path.join(BASE_DIR, 'runtime.log')
            ),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': os.environ.get('LOGGING_DJANGO_REQUEST_LEVEL', 'WARNING'),
            'propagate': True,
        },
        'ralph': {
            'handlers': ['file'],
            'level': os.environ.get('LOGGING_RALPH_LEVEL', 'WARNING'),
            'propagate': True,
        },
        'rq.worker': {
            'level': os.environ.get('LOGGING_RQ_LEVEL', 'WARNING'),
            'handlers': ['file'],
            'propagate': True,
        }
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'ralph.lib.permissions.api.RalphPermission',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'ralph.lib.permissions.api.PermissionsForObjectFilter',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_xml.renderers.XMLRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework_xml.parsers.XMLParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',  # noqa
    'PAGE_SIZE': 10,
    'DEFAULT_METADATA_CLASS': 'ralph.lib.api.utils.RalphApiMetadata',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',  # noqa
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ('v1',)
}

REDIS_CONNECTION = {
    'HOST': os.environ.get('REDIS_HOST', 'localhost'),
    'PORT': os.environ.get('REDIS_PORT', '6379'),
    'DB': int(os.environ.get('REDIS_DB', 0)),
}

BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME = True

TAGGIT_CASE_INSENSITIVE = True  # case insensitive tags

RALPH_EXTERNAL_SERVICES = {
    'PDF': {
        'name': 'ralph_ext_pdf',
        'method': 'inkpy_jinja.pdf',
    }
}
