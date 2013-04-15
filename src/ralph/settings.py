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
USE_L10N = True  # FIXME: breaks contents of localized date fields on form reload
MEDIA_URL = '/u/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    CURRENT_DIR + 'media',
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'lck.django.staticfiles.LegacyAppDirectoriesFinder',
)
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
    'django_rq',
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
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
            'backupCount': 10,
            'filename': None,  # to be configured in settings-local.py
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
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
# testing settings
import os
import ralph
TEST_DISCOVERY_ROOT = os.path.realpath(os.path.dirname(ralph.__file__))
TEST_RUNNER = b'ralph.util.DiscoveryDjangoTestSuiteRunner'
# django.contrib.auth settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)
AUTH_PROFILE_MODULE = 'account.Profile'
LOGIN_REDIRECT_URL = '/browse/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
HOME_PAGE_URL_NAME = 'search'
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
# define the lookup channels in use on the site
AJAX_LOOKUP_CHANNELS = {
    'ci': ('ralph.cmdb.models', 'CILookup'),
    'device': ('ralph.ui.channels', 'DeviceLookup'),
}
# magically include jqueryUI/js/css
AJAX_SELECT_BOOTSTRAP = True
AJAX_SELECT_INLINES = 'inline'

#
# stuff that should be customized in local settings
#

# <template>
SECRET_KEY = 'CHANGE ME'
DEBUG = False
TEMPLATE_DEBUG = False
SEND_BROKEN_LINK_EMAILS = False
ADMINS = (
    #('Webmaster', 'ralph@localhost'),
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
MEDIA_ROOT = '~/.ralph/shared/uploads'
STATIC_ROOT = '~/.ralph/shared/static'
FILE_UPLOAD_TEMP_DIR = '~/.ralph/shared/uploads-part'
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
SSH_USER = None
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
XEN_USER = None
XEN_PASSWORD = None
SNMP_PLUGIN_COMMUNITIES = ['public']
SNMP_V3_USER = None
SNMP_V3_AUTH_KEY = None
SNMP_V3_PRIV_KEY = None
DEFAULT_SAVE_PRIORITY = 0
SCCM_DB_URL = None
SSH_MSA_USER = None
SSH_MSA_PASSWORD = None
SSH_P2000_USER = None
SSH_P2000_PASSWORD = None
SPLUNK_HOST = None
SPLUNK_USER = None
SPLUNK_PASSWORD = None
SPLUNK_LOGGER_PORT = None
SPLUNK_LOGGER_HOST = None
PUPPET_DB_URL = None
PUPPET_API_URL = None
ZABBIX_URL = None
ZABBIX_USER = None
ZABBIX_PASSWORD = None
ZABBIX_DEFAULT_GROUP = 'test'
BUGTRACKER_URL = 'https://github.com/allegro/ralph/issues/new'
SO_URL = None
OPENSTACK_URL = None
OPENSTACK_USER = None
OPENSTACK_PASS = None
IBM_SYSTEM_X_USER = None
IBM_SYSTEM_X_PASSWORD = None
IDRAC_USER = None
IDRAC_PASSWORD = None
OPENSTACK_EXTRA_QUERIES = []
FISHEYE_URL = ""
FISHEYE_PROJECT_NAME = ""

ISSUETRACKERS = {
    'default': {
        'ENGINE': '',
        'USER': '',
        'PASSWORD': '',
        'URL': '',
        'CI_FIELD_NAME': '',
        'CI_NAME_FIELD_NAME': '',
        'TEMPLATE_FIELD_NAME': '',
        'PROFILE_FIELD_NAME': '',
        'IMPACT_ANALYSIS_FIELD_NAME': '',
        'PROBLEMS_FIELD_NAME': '',
        'CMDB_PROJECT': '',
        'CMDB_VIEWCHANGE_LINK': 'http://url/%s',
        'ENQUEUE_REGISTRATION': True,
        'OPA': {
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
            'ENABLE_TICKETS': False,
            'START_DATE': '',
            'ISSUETYPE': '',
            'TEMPLATE': '',
            'PROFILE': '',
            'DEFAULT_ASSIGNEE': '',
        },
    },
}
API_THROTTLING = {
    'throttle_at': 200,
    'timeframe': 3600,
    'expiration': None,
}
RQ_QUEUE_LIST = ('reports', 'email', 'cmdb_git', 'cmdb_jira', 'cmdb_jira_int',
                 'cmdb_zabbix', 'cmdb_assets')
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    },
}
for queue in RQ_QUEUE_LIST:
    RQ_QUEUES[queue] = dict(RQ_QUEUES['default'])
AUTOCI = True
AUTOCI_SKIP_MSG = 'AUTOCI is disabled'
# </template>

#
# programmatic stuff that need to be at the end of the file
#
import os
local_profile = os.environ.get('DJANGO_SETTINGS_PROFILE', 'local')
ralph_settings_path = os.environ.get('RALPH_SETTINGS_PATH', '~/.ralph')

if SETTINGS_PATH_MODE == 'flat':
    local_settings = '%s-%s.py' % (SETTINGS_PATH_PREFIX, local_profile)
elif SETTINGS_PATH_MODE == 'nested':
    local_settings = '%s%s%s.py' % (SETTINGS_PATH_PREFIX, os.sep,
                                    local_profile)
else:
    raise ValueError, ("Unsupported settings path mode '%s'"
                       "" % SETTINGS_PATH_MODE)

for cfg_loc in [local_settings,
                '{}/settings'.format(ralph_settings_path),
                '/etc/ralph/settings']:
    cfg_loc = os.path.expanduser(cfg_loc)
    if os.path.exists(cfg_loc):
        execfile(cfg_loc)
        break

MEDIA_ROOT = os.path.expanduser(MEDIA_ROOT)
STATIC_ROOT = os.path.expanduser(STATIC_ROOT)
FILE_UPLOAD_TEMP_DIR = os.path.expanduser(FILE_UPLOAD_TEMP_DIR)

for path in (MEDIA_ROOT, STATIC_ROOT, FILE_UPLOAD_TEMP_DIR):
    try:
        os.makedirs(path)
    except (IOError, OSError):
        continue
