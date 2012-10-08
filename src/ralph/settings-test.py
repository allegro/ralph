#
# A testing profile.
#
SECRET_KEY = 'Ralph--remember what we came for. The fire. My specs.'
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DUMMY_SEND_MAIL = DEBUG
SEND_BROKEN_LINK_EMAILS = DEBUG
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
#LOGGING['handlers']['file']['filename'] = CURRENT_DIR + 'runtime.log'
BROKER_HOST = "localhost"
BROKER_PORT = 25672
BROKER_USER = "ralph"
BROKER_PASSWORD = "ralph"
BROKER_VHOST = "/ralph"
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
#   slows down testing - disabled
#   'djcelery',
    'south',
    'lck.django.common',
#   slows down testing - disabled
    'lck.django.activitylog',
    'lck.django.profile',
    'lck.django.score',
    'lck.django.tags',
    'gunicorn',
    'fugue_icons',
    'bob',
#   slows down testing - disabled
    'tastypie',
    'ralph.account',
    'ralph.business',
    'ralph.cmdb',
    'ralph.discovery',
    'ralph.integration',
    'ralph.ui',
    'ralph.dnsedit',
    'ralph.util',
    'ralph.deployment',
    'ajax_select',
    'powerdns',
]


ISSUETRACKERS = {
    'default': {
        'ENGINE': '',
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
    'JIRA': {
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

from lck.django import current_dir_support
execfile(current_dir_support)

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
ZABBIX_URL = None
ZABBIX_USER = None
ZABBIX_PASSWORD = None
ZABBIX_DEFAULT_GROUP = ''
BUGTRACKER_URL = ''

SO_URL = None
OPENSTACK_URL = None
OPENSTACK_USER = None
OPENSTACK_PASS = None
OPENSTACK_EXTRA_QUERIES = []

SANITY_CHECK_PING_ADDRESS=''
SANITY_CHECK_IP2HOST_IP=''
SANITY_CHECK_IP2HOST_HOSTNAME_REGEX = r'.*google.*'

API_THROTTLING = {
    'throttle_at': 2,
    'timeframe': 10,
    'expiration': None,
}
IBM_SYSTEM_X_USER = ""
IBM_SYSTEM_X_PASSWORD = ""
