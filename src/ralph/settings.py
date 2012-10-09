#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Django settings for Ralph. Customize the middle section and save it
   in settings-local.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.django import current_dir_support
execfile(current_dir_support)

from lck.django import namespace_package_support
execfile(namespace_package_support)

#
# common stuff for each install
#
SITE_ID = 1
USE_I18N = True
USE_L10N = True #FIXME: breaks contents of localized date fields on form reload
MEDIA_ROOT = CURRENT_DIR + 'uploads'
MEDIA_URL = '/u/'
STATIC_ROOT = CURRENT_DIR + 'static'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    CURRENT_DIR + 'media',
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'lck.django.staticfiles.LegacyAppDirectoriesFinder',
)
FILE_UPLOAD_TEMP_DIR = CURRENT_DIR + 'uploads-part'
USE_XSENDFILE = False
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'lck.django.common.middleware.TimingMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'lck.django.activitylog.middleware.ActivityMiddleware',
    'lck.django.common.middleware.ForceLanguageCodeMiddleware',
)
ROOT_URLCONF = 'ralph.urls'
TEMPLATE_DIRS = (CURRENT_DIR + "templates",)
LOCALE_PATHS = (CURRENT_DIR + "locale",)
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'djcelery',
    'south',
    'lck.django.common',
    'lck.django.activitylog',
    'lck.django.profile',
    'lck.django.score',
    'lck.django.tags',
    'gunicorn',
    'fugue_icons',
    'bob',
    'tastypie',
    'ralph.account',
    'ralph.business',
    'ralph.cmdb',
    'ralph.discovery',
    'ralph.deployment',
    'ralph.integration',
    'ralph.ui',
    'ralph.dnsedit',
    'ralph.util',
    'ralph.deployment',
    'ajax_select',
    'powerdns',
]
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
)
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 100, # 100 MB
            'backupCount': 10,
            'filename': None, # to be configured in settings-local.py
            'formatter': 'verbose',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'formatters': {
        'verbose': {
            'datefmt': '%H:%M:%S',
            'format': '%(asctime)08s,%(msecs)03d %(levelname)-7s [%(processName)s %(process)d] %(module)s - %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'ralph': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'critical_only': {
            'handlers': ['file', 'mail_admins'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
}
FORCE_SCRIPT_NAME = ''
# django.contrib.auth settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)
AUTH_PROFILE_MODULE = 'account.Profile'
LOGIN_REDIRECT_URL = '/browse/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
SANITY_CHECK_PING_ADDRESS = 'www.allegro.pl'
SANITY_CHECK_IP2HOST_IP = '8.8.8.8'
SANITY_CHECK_IP2HOST_HOSTNAME_REGEX = r'.*google.*'

SINGLE_DISCOVERY_TIMEOUT = 43200 # 12 hours
NETWORK_TASK_DELEGATION_TIMEOUT = 7200 # 2 hours
# django.contrib.messages settings
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
# activity middleware settings
CURRENTLY_ONLINE_INTERVAL = 300
RECENTLY_ONLINE_INTERVAL = 900
ACTIVITYLOG_PROFILE_MODEL = AUTH_PROFILE_MODULE
# lck.django.common models
EDITOR_TRACKABLE_MODEL = AUTH_PROFILE_MODULE
# lck.django.score models
SCORE_VOTER_MODEL = AUTH_PROFILE_MODULE
# lck.django.tags models
TAG_AUTHOR_MODEL = AUTH_PROFILE_MODULE
# Celery
from multiprocessing import cpu_count
CELERYD_CONCURRENCY = min(4 * cpu_count(), 32)
BROKER_POOL_LIMIT = 4 * CELERYD_CONCURRENCY
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_RESULT_BACKEND = "disabled"
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_POOL_PUTLOCKS = False
CELERYD_FORCE_EXECV = False
CELERYD_TASK_TIME_LIMIT = 900
CELERY_ROUTES = (
    "ralph.discovery.tasks.DCRouter",
)
# define the lookup channels in use on the site
AJAX_LOOKUP_CHANNELS = {
    'ci'  : {'model':'cmdb.CI', 'search_field':'name'}
}
# magically include jqueryUI/js/css
AJAX_SELECT_BOOTSTRAP = True
AJAX_SELECT_INLINES = 'inline'

#
# stuff that should be customized in local settings
#

# <template>
SECRET_KEY = 'CHANGE ME'
DEBUG = True#False
TEMPLATE_DEBUG = DEBUG
SEND_BROKEN_LINK_EMAILS = DEBUG
ADMINS = (
    ('Webmaster', 'ralph@localhost'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = 'ralph@localhost'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
TIME_ZONE = 'Europe/Warsaw'
LANGUAGE_CODE = 'en-us'
CURRENCY = 'PLN'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': CURRENT_DIR + 'dbralph.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': dict(
        ),
    },
}
CACHES = dict(
    default = dict(
        BACKEND = 'django.core.cache.backends.locmem.LocMemCache',
        LOCATION = '',
        TIMEOUT = 300,
        OPTIONS = dict(
        ),
        KEY_PREFIX = 'RALPH_',
    )
)
LOGGING['handlers']['file']['filename'] = CURRENT_DIR + 'runtime.log'
BROKER_URL = "sqla+sqlite:///" + CURRENT_DIR + 'dbcelery.sqlite'
SYNERGY_URL_BASE = "/"
DASHBOARD_SITE_DOMAIN = "dashboard.local"
IPMI_USER = None
IPMI_PASSWORD = None
F5_USER = None
F5_PASSWORD = None
F5_USER2 = None
F5_PASSWORD2 = None
ILO_USER = None
ILO_PASSWORD = None
SSH_PASSWORD = None
SSH_IBM_USER = None
SSH_IBM_PASSWORD = None
SSH_SSG_USER = None
SSH_SSG_PASSWORD = None
SSH_3PAR_USER = None
SSH_3PAR_PASSWORD = None
SSH_ONSTOR_USER = None
SSH_ONSTOR_PASSWORD = None
AIX_USER = None
AIX_PASSWORD = None
AIX_KEY = None
XEN_USER=None
XEN_PASSWORD = None
SNMP_PLUGIN_COMMUNITIES = ['public']
DEFAULT_SAVE_PRIORITY = 0
SCCM_DB_URL=None
SSH_MSA_USER = None
SSH_MSA_PASSWORD = None
SSH_P2000_USER = None
SSH_P2000_PASSWORD = None
SPLUNK_HOST = None
SPLUNK_USER = None
SPLUNK_PASSWORD = None
PUPPET_DB_URL = None
PUPPET_SAVE_UNCHANGED_RESOURCES = False
ZABBIX_URL = None
ZABBIX_USER = None
ZABBIX_PASSWORD = None
ZABBIX_DEFAULT_GROUP = 'test'
BUGTRACKER_URL = 'https://github.com/allegro/ralph/issues'
SO_URL = None
OPENSTACK_URL = None
OPENSTACK_USER = None
OPENSTACK_PASS = None
IBM_SYSTEM_X_USER = None
IBM_SYSTEM_X_PASSWORD = None
OPENSTACK_EXTRA_QUERIES = []
FISHEYE_URL = ""
FISHEYE_PROJECT_NAME = ""
ISSUETRACKERS = {
    'default': {
        'ENGINE': 'JIRA',
        'USER': '',
        'PASSWORD': '',
        'URL': '',
        'CI_FIELD_NAME': '',
        'CI_NAME_FIELD_NAME': '',
        'TEMPLATE_FIELD_NAME': '',
        'CMDB_PROJECT': '',
        'CMDB_VIEWCHANGE_LINK': '',
        'OPA': {
                'RSS_URL' : '',
                'BOWNER_FIELD_NAME': '',
                'TOWNER_FIELD_NAME': '',
                'TEMPLATE': '',
                'ISSUETYPE': '',
                'DEFAULT_ASSIGNEE': '',
                'ACTIONS': {
                    'IN_PROGRESS': 1,
                    'IN_DEPLOYMENT': 2,
                    'RESOLVED_FIXED': 3,
                },
        },
        'OP': {
                'ISSUETYPE': '',
                'TEMPLATE': '',
                'DEFAULT_ASSIGNEE': '',
        },
    },
}
API_THROTTLING = {
    'throttle_at': 200,
    'timeframe': 3600,
    'expiration': None,
}
# </template>

#
# programmatic stuff that need to be at the end of the file
#
import djcelery
djcelery.setup_loader()

import os
local_profile = os.environ.get('DJANGO_SETTINGS_PROFILE', 'local')

if SETTINGS_PATH_MODE == 'flat':
    local_settings = '%s-%s.py' % (SETTINGS_PATH_PREFIX, local_profile)
elif SETTINGS_PATH_MODE == 'nested':
    local_settings = '%s%s%s.py' % (SETTINGS_PATH_PREFIX, os.sep,
                                    local_profile)
else:
    raise ValueError, ("Unsupported settings path mode '%s'"
                       "" % SETTINGS_PATH_MODE)

for cfg_loc in [local_settings,
                '~/.ralph/settings',
                '/etc/ralph/settings']:
    cfg_loc = os.path.expanduser(cfg_loc)
    if os.path.exists(cfg_loc):
        execfile(cfg_loc)
        break
