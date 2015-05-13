# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'qbyqnpi58brjo=!l+)jza*z@r-!ba6w2yhmj=)9%qr5ymtcy_9'

DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'polymorphic',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'reversion',
    'ralph.assets',
    'ralph.backoffice',
    'ralph.datacenter'
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
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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
        'NAME': 'ralph_ng',
        'USER': 'ralph_ng',
        'PASSWORD': 'ralph_ng',
        'HOST': '127.0.0.1',
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

from django.contrib.messages import constants as messages
# adapt message's tags to bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.ERROR: 'danger',
}

# SUIT_CONFIG = {
#     'ADMIN_NAME': 'Ralph NG',
#     'MENU': (
#         {
#             'label': 'Configuration',
#             'icon': 'icon-book',
#             'models': (
#                 'assets.assetmodel',
#                 'assets.category',
#                 'assets.service',
#                 'assets.environment',
#             )
#         },
#         {
#             'label': 'Data center',
#             'icon': 'icon-tasks',
#             'models': (
#                 'assets.dcasset',
#                 'assets.cloudproject',
#                 'assets.database',
#                 'assets.vip',
#                 'assets.virtualserver',
#             )
#         },
#         {
#             'label': 'Back office',
#             'icon': 'icon-print',
#             'models': (
#                 'assets.boasset',
#                 'assets.warehouse',
#             )
#         },
#         '-',
#         {'app': 'auth', 'icon': 'icon-user'},
#     )
# }


DEFAULT_DEPRECATION_RATE = 25
ASSET_HOSTNAME_TEMPLATE = 'test'
