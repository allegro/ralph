# -*- coding: utf-8 -*-
import json
import os
from collections import ChainMap
from datetime import datetime

from django.contrib.messages import constants as messages
from moneyed import CURRENCIES

from ralph.settings.hooks import HOOKS_CONFIGURATION  # noqa: F401

SILENCED_SYSTEM_CHECKS = [
    "models.E006",
]  # TODO fix


def bool_from_env(var, default: bool = False) -> bool:
    """Helper for converting env string into boolean.

    Returns bool True for string values: '1' or 'true', False otherwise.
    """

    def str_to_bool(s: str) -> bool:
        return s.lower() in ("1", "true")

    os_var = os.environ.get(var)
    if os_var is None:
        # as user expect
        return default
    else:
        return str_to_bool(os_var)


def get_sentinels(sentinels_string):
    """Helper for converting sentinel hosts string into list of tuples.

    sentinel_string must be a string in the following format:
    <sentinel_ip>:<sentinel_port>;<sentinel_ip>:<sentinel_port>

    Returns a list of sentinel host and port tuples
    """
    if sentinels_string:
        sentinels = sentinels_string.split(";")
        result = [tuple(sentinel.split(":")) for sentinel in sentinels]
        return result


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

START_TIMESTAMP = datetime.now()
SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_ME")
LOG_FILEPATH = os.environ.get("LOG_FILEPATH", "/tmp/ralph.log")

DEBUG = False

ALLOWED_HOSTS = ["*"]

# Only for deployment
RALPH_INSTANCE = os.environ.get("RALPH_INSTANCE", "http://127.0.0.1:8000")

# Application definition

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "taggit",
    "django.contrib.auth",
    "ralph.admin",
    "django.contrib.admin",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "django_rq",
    "import_export",
    "mptt",
    "reversion",
    "sitetree",
    "ralph.access_cards",
    "ralph.accounts",
    "ralph.accessories",
    "ralph.assets",
    "ralph.attachments",
    "ralph.back_office",
    "ralph.configuration_management",
    "ralph.dashboards",
    "ralph.data_center",
    "ralph.dhcp",
    "ralph.deployment",
    "ralph.licences",
    "ralph.domains",
    "ralph.trade_marks",
    "ralph.sim_cards",
    "ralph.supports",
    "ralph.security",
    "ralph.lib.foundation",
    "ralph.lib.table",
    "ralph.networks",
    "ralph.data_importer",
    "ralph.dc_view",
    "ralph.reports",
    "ralph.virtual",
    "ralph.operations",
    "ralph.lib.external_services",
    "ralph.lib.transitions",
    "ralph.lib.permissions",
    "ralph.lib.custom_fields",
    "ralph.lib.hooks",
    "ralph.notifications",
    "ralph.ssl_certificates",
    "rest_framework",
    "rest_framework.authtoken",
    "taggit_serializer",
    "djmoney",
)

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "ralph.lib.threadlocal.middleware.ThreadLocalMiddleware",
    "ralph.lib.metrics.middlewares.RequestMetricsMiddleware",
)

ROOT_URLCONF = "ralph.urls"
URLCONF_MODULES = [ROOT_URLCONF]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                        "ralph.lib.template.loaders.AppTemplateLoader",
                    ],
                ),
            ],
        },
    },
]

WSGI_APPLICATION = "ralph.wsgi.application"

DEFAULT_DATABASE_OPTIONS = {
    "sql_mode": "TRADITIONAL",
    "charset": "utf8",
    "init_command": """
    SET default_storage_engine=INNODB;
    SET character_set_connection=utf8,collation_connection=utf8_unicode_ci;
    SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
    """,
}
DATABASE_OPTIONS_FROM_ENV = os.environ.get("DATABASE_OPTIONS", None)
DATABASE_OPTIONS = (
    json.loads(DATABASE_OPTIONS_FROM_ENV)
    if DATABASE_OPTIONS_FROM_ENV
    else DEFAULT_DATABASE_OPTIONS
)

DATABASE_SSL_CA = os.environ.get("DATABASE_SSL_CA", None)
if DATABASE_SSL_CA:
    DATABASE_OPTIONS.update({"ssl": {"ca": DATABASE_SSL_CA}})

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DATABASE_ENGINE", "django.db.backends.mysql"),  # noqa
        "NAME": os.environ.get("DATABASE_NAME", "ralph_ng"),
        "USER": os.environ.get("DATABASE_USER", "ralph_ng"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "ralph_ng") or None,
        "HOST": os.environ.get("DATABASE_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DATABASE_PORT", 3306),
        "OPTIONS": DATABASE_OPTIONS,
        "ATOMIC_REQUESTS": True,
        "TEST": {
            "NAME": "test_ralph_ng",
        },
    }
}

AUTH_USER_MODEL = "accounts.RalphUser"
LOGIN_URL = "/login/"

LANGUAGE_CODE = "en-us"
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)
TIME_ZONE = "Europe/Warsaw"
USE_I18N = bool_from_env("USE_I18N", True)
USE_L10N = bool_from_env("USE_L10N", True)
USE_TZ = False

STATIC_URL = "/static/"
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "admin", "static"),
)
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(BASE_DIR, "var", "static"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", os.path.join(BASE_DIR, "var", "media"))

# adapt message's tags to bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.ERROR: "alert",
}
FILE_UPLOAD_PERMISSIONS = 0o644

DEFAULT_DEPRECIATION_RATE = int(os.environ.get("DEFAULT_DEPRECIATION_RATE", 25))  # noqa
DEFAULT_LICENCE_DEPRECIATION_RATE = int(
    os.environ.get("DEFAULT_LICENCE_DEPRECIATION_RATE", 50)
)  # noqa
CHECK_IP_HOSTNAME_ON_SAVE = bool_from_env("CHECK_IP_HOSTNAME_ON_SAVE", True)
ASSET_HOSTNAME_TEMPLATE = {
    "prefix": "{{ country_code|upper }}{{ code|upper }}",
    "postfix": "",
    "counter_length": 5,
}
DEFAULT_COUNTRY_CODE = os.environ.get("DEFAULT_COUNTRY_CODE", "POL")


LDAP_SERVER_OBJECT_USER_CLASS = "user"  # possible values: user, person

ADMIN_SITE_HEADER = "Ralph 3"
ADMIN_SITE_TITLE = "Ralph 3"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "datefmt": "%d.%m.%Y %H:%M:%S",
            "format": (
                "[%(asctime)08s,%(msecs)03d] %(levelname)-7s [%(processName)s"
                " %(process)d] %(module)s - %(message)s"
            ),
        },
        "simple": {
            "datefmt": "%H:%M:%S",
            "format": "[%(asctime)08s] %(levelname)-7s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 10,
            "filename": os.environ.get("LOG_FILEPATH", LOG_FILEPATH),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["file"],
            "level": os.environ.get("LOGGING_DJANGO_REQUEST_LEVEL", "WARNING"),
            "propagate": True,
        },
        "ralph": {
            "handlers": ["file"],
            "level": os.environ.get("LOGGING_RALPH_LEVEL", "WARNING"),
            "propagate": True,
        },
        "rq.worker": {
            "level": os.environ.get("LOGGING_RQ_LEVEL", "WARNING"),
            "handlers": ["file"],
            "propagate": True,
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("ralph.lib.permissions.api.RalphPermission",),
    "DEFAULT_FILTER_BACKENDS": (
        "ralph.lib.permissions.api.PermissionsForObjectFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "ralph.lib.api.utils.NoFiltersBrowsableAPIRenderer",
        "rest_framework_xml.renderers.XMLRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework_xml.parsers.XMLParser",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",  # noqa
    "PAGE_SIZE": 10,
    "DEFAULT_METADATA_CLASS": "ralph.lib.api.utils.RalphApiMetadata",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",  # noqa
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ("v1",),
    "EXCEPTION_HANDLER": "ralph.lib.api.exception_handler.validation_error_exception_handler",  # noqa
}

API_THROTTLING = bool_from_env("API_THROTTLING", default=False)
if API_THROTTLING:
    REST_FRAMEWORK.update(
        {
            "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.UserRateThrottle",),
            "DEFAULT_THROTTLE_RATES": {
                "user": os.environ.get("API_THROTTLING_USER", "5000/hour")
            },
        }
    )

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "ralph_ng")
REDIS_SENTINEL_ENABLED = bool_from_env("REDIS_SENTINEL_ENABLED", False)
REDIS_SOCKET_TIMEOUT = float(os.environ.get("REDIS_SOCKET_TIMEOUT", 1.0))
REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", 1.0))
REDIS_COMMAND_TIMEOUT = float(os.environ.get("REDIS_COMMAND_TIMEOUT", 10.0))

if REDIS_SENTINEL_ENABLED:
    from redis.sentinel import Sentinel

    REDIS_SENTINEL_HOSTS = get_sentinels(os.environ.get("REDIS_SENTINEL_HOSTS", None))  # noqa
    REDIS_CLUSTER_NAME = os.environ.get("REDIS_CLUSTER_NAME", "ralph_ng")
    REDIS_SENTINEL_SOCKET_TIMEOUT = float(
        os.environ.get("REDIS_SENTINEL_SOCKET_TIMEOUT", 1.0)
    )  # noqa

    sentinel = Sentinel(
        REDIS_SENTINEL_HOSTS,
        socket_timeout=REDIS_SENTINEL_SOCKET_TIMEOUT,
        password=REDIS_PASSWORD,
    )
    REDIS_MASTER = sentinel.master_for(REDIS_CLUSTER_NAME)

    REDIS_CONNECTION = {
        "SENTINELS": REDIS_SENTINEL_HOSTS,
        "DB": int(os.environ.get("REDIS_DB", 0)),
        "PASSWORD": REDIS_PASSWORD,
        "TIMEOUT": REDIS_COMMAND_TIMEOUT,
        "CONNECT_TIMEOUT": REDIS_CONNECT_TIMEOUT,
    }
    RQ_QUEUES = {
        "default": {
            "SENTINELS": REDIS_SENTINEL_HOSTS,
            "MASTER_NAME": REDIS_CLUSTER_NAME,
            "DB": int(os.environ.get("REDIS_DB", 0)),
            "PASSWORD": REDIS_PASSWORD,
            "CONNECTION_KWARGS": {
                "socket_connect_timeout": REDIS_CONNECT_TIMEOUT,
                "retry_on_timeout": True,
            },
        },
    }
else:
    REDIS_MASTER_IP = None
    REDIS_MASTER_PORT = None
    REDIS_CONNECTION = {
        "HOST": REDIS_MASTER_IP or os.environ.get("REDIS_HOST", "localhost"),  # noqa
        "PORT": REDIS_MASTER_PORT or os.environ.get("REDIS_PORT", "6379"),
        "DB": int(os.environ.get("REDIS_DB", 0)),
        "PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
        "TIMEOUT": REDIS_COMMAND_TIMEOUT,
        "CONNECT_TIMEOUT": REDIS_CONNECT_TIMEOUT,
    }
    RQ_QUEUES = {"default": dict(**REDIS_CONNECTION)}

# set to False to turn off cache decorator
USE_CACHE = bool_from_env("USE_CACHE", True)

SENTRY_ENABLED = bool_from_env("SENTRY_ENABLED")

BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME = bool_from_env(
    "BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME", False
)

BACKOFFICE_HOSTNAME_FIELD_READONLY = bool_from_env(
    "BACKOFFICE_HOSTNAME_FIELD_READONLY", False
)

TAGGIT_CASE_INSENSITIVE = True  # case insensitive tags

RALPH_QUEUES = {
    "ralph_ext_pdf": {},
    "ralph_async_transitions": {
        "DEFAULT_TIMEOUT": 3600,
    },
}
for queue_name, options in RALPH_QUEUES.items():
    RQ_QUEUES[queue_name] = ChainMap(RQ_QUEUES["default"], options)


RALPH_EXTERNAL_SERVICES = {
    "PDF": {
        "queue_name": "ralph_ext_pdf",
        "method": "inkpy_jinja.pdf",
    },
}

RALPH_INTERNAL_SERVICES = {
    "ASYNC_TRANSITIONS": {
        "queue_name": "ralph_async_transitions",
        "method": "ralph.lib.transitions.async.run_async_transition",
    }
}

# =============================================================================
# DC view
# =============================================================================

RACK_LISTING_NUMBERING_TOP_TO_BOTTOM = False

# =============================================================================
# Deployment
# =============================================================================

DEPLOYMENT_MAX_DNS_ENTRIES_TO_CLEAN = 30

# =============================================================================

# Example:
# MY_EQUIPMENT_LINKS = [
#     {'url': 'http://....', 'name': 'Link name'},
# ]
MY_EQUIPMENT_LINKS = json.loads(os.environ.get("MY_EQUIPMENT_LINKS", "[]"))
MANAGING_DEVICES_MOVED_INFO = os.environ.get("MANAGING_DEVICES_MOVED_INFO", "")  # noqa
MY_EQUIPMENT_REPORT_FAILURE_URL = os.environ.get("MY_EQUIPMENT_REPORT_FAILURE_URL", "")  # noqa
MY_EQUIPMENT_SHOW_BUYOUT_DATE = bool_from_env("MY_EQUIPMENT_SHOW_BUYOUT_DATE")
MY_EQUIPMENT_BUYOUT_URL = os.environ.get("MY_EQUIPMENT_BUYOUT_URL", "")

# Sets URL shown to user if they declare that they dp not have specific asset.
MISSING_ASSET_REPORT_URL = os.environ.get("MISSING_ASSET_REPORT_URL", None)

# Redirect to result detail view if there is only one in search result list
REDIRECT_TO_DETAIL_VIEW_IF_ONE_SEARCH_RESULT = bool_from_env(
    "REDIRECT_TO_DETAIL_VIEW_IF_ONE_SEARCH_RESULT", True
)

# Stocktaking tagging config - each variable describes individual tag.
# To disable tag set it to None or, in case of date tag, set variable to '0'.
INVENTORY_TAG = os.environ.get("INVENTORY_TAG", "INV")
# This tag means user himself confirmed asset possession.
INVENTORY_TAG_USER = os.environ.get("INVENTORY_TAG_USER", "INV_CONF")
INVENTORY_TAG_MISSING = os.environ.get("INVENTORY_TAG_MISSING", "INV_MISSING")
INVENTORY_TAG_APPEND_DATE = bool_from_env("INVENTORY_TAG_APPEND_DATE", True)

ENABLE_ACCEPT_ASSETS_FOR_CURRENT_USER = bool_from_env(
    "ENABLE_ACCEPT_ASSETS_FOR_CURRENT_USER"
)  # noqa
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG = {
    "TRANSITION_ID": os.environ.get(
        "ACCEPT_ASSETS_FOR_CURRENT_USER_TRANSITION_ID", None
    ),
    "TRANSITION_SIM_ID": os.environ.get("ACCEPT_SIMCARD_FOR_CURRENT_USER_CONFIG", None),
    "TRANSITION_ACCESS_CARD_ID": os.environ.get(
        "ACCEPT_ACCESS_CARD_FOR_CURRENT_USER_CONFIG", None
    ),
    # in_progress by default
    "BACK_OFFICE_ACCEPT_STATUS": os.environ.get(
        "ACCEPT_ASSETS_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 2
    ),
    "SIMCARD_ACCEPT_STATUS": os.environ.get(
        "SIMCARD_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 2
    ),
    "ACCESS_CARD_ACCEPT_ACCEPT_STATUS": os.environ.get(
        "ACCESS_CARD_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 2
    ),
    "LOAN_TRANSITION_ID": os.environ.get(
        "LOAN_ASSETS_FOR_CURRENT_USER_TRANSITION_ID", None
    ),
    # loan_in_progress by default
    "BACK_OFFICE_ACCEPT_LOAN_STATUS": os.environ.get(
        "LOAN_ASSETS_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 13
    ),
    "RETURN_TRANSITION_ID": os.environ.get(
        "RETURN_ASSETS_FOR_CURRENT_USER_TRANSITION_ID", None
    ),
    # waiting_for_return by default
    "BACK_OFFICE_ACCEPT_RETURN_STATUS": os.environ.get(
        "RETURN_ASSESTS_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 14
    ),
    "BACK_OFFICE_TEAM_ACCEPT_STATUS": os.environ.get(
        "ACCEPT_TEAM_ASSETS_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 20
    ),
    "TRANSITION_TEAM_ACCEPT_ID": os.environ.get(
        "ACCEPT_TEAM_ASSETS_FOR_CURRENT_USER_TRANSITION_ID", None
    ),
    "BACK_OFFICE_TEST_ACCEPT_STATUS": os.environ.get(
        "ACCEPT_TEST_ASSETS_FOR_CURRENT_USER_BACK_OFFICE_ACCEPT_STATUS", 21
    ),
    "TRANSITION_TEST_ACCEPT_ID": os.environ.get(
        "ACCEPT_TEST_ASSETS_FOR_CURRENT_USER_TRANSITION_ID", None
    ),
}
RELEASE_REPORT_CONFIG = {
    # report with name 'release' is by default
    "DEFAULT_REPORT": os.environ.get("RELEASE_REPORT_CONFIG_DEFAULT_REPORT", "release"),
    # map transition id to different report
    "REPORTS_MAPPER": json.loads(
        os.environ.get("RELEASE_REPORT_CONFIG_REPORTS_MAPPER", "{}")
    ),
}

MAP_IMPORTED_ID_TO_NEW_ID = False

OPENSTACK_INSTANCES = json.loads(os.environ.get("OPENSTACK_INSTANCES", "[]"))
DEFAULT_OPENSTACK_PROVIDER_NAME = os.environ.get(
    "DEFAULT_OPENSTACK_PROVIDER_NAME", "openstack"
)
# issue tracker url for Operations urls (issues ids) - should end with /
ISSUE_TRACKER_URL = os.environ.get("ISSUE_TRACKER_URL", "")

# Networks
DEFAULT_NETWORK_BOTTOM_MARGIN = int(os.environ.get("DEFAULT_NETWORK_BOTTOM_MARGIN", 10))  # noqa
DEFAULT_NETWORK_TOP_MARGIN = int(os.environ.get("DEFAULT_NETWORK_TOP_MARGIN", 0))  # noqa
# deprecated, to remove in the future
DEFAULT_NETWORK_MARGIN = int(os.environ.get("DEFAULT_NETWORK_MARGIN", 10))
# when set to True, network records (IP/Ethernet) can't be modified until
# 'expose in DHCP' is selected
DHCP_ENTRY_FORBID_CHANGE = bool_from_env("DHCP_ENTRY_FORBID_CHANGE", True)

# disable integration with DNSaaS as it's no longer supported
# https://github.com/allegro/django-powerdns-dnssec
# This settings will be deleted in future release.
ENABLE_DNSAAS_INTEGRATION = False
DNSAAS_URL = os.environ.get("DNSAAS_URL", "")
DNSAAS_TOKEN = os.environ.get("DNSAAS_TOKEN", "")
DNSAAS_TIMEOUT = os.environ.get("DNSAAS_TIMEOUT", 10)
DNSAAS_AUTO_PTR_ALWAYS = os.environ.get("DNSAAS_AUTO_PTR_ALWAYS", 2)
DNSAAS_AUTO_PTR_NEVER = os.environ.get("DNSAAS_AUTO_PTR_NEVER", 1)
# user in dnsaas which can do changes, like update TXT records etc.
DNSAAS_OWNER = os.environ.get("DNSAAS_OWNER", "ralph")
# pyhermes topic where messages about auto txt records are announced
DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME = None
# define names of values send to DNSAAS for:
# DataCenterAsset, Cluster, VirtualServer
DNSAAS_AUTO_TXT_RECORD_PURPOSE_MAP = {
    # self.configuration_path.class will be send as 'VENTURE'
    "class_name": "VENTURE",
    # self.configuration_path.module will be send as 'ROLE'
    "module_name": "ROLE",
    # self.configuration_path.path will be send as 'PATH'
    "configuration_path": "CONFIGURATION_PATH",
    # self.service_env will be send as 'SERVICE_ENV'
    "service_env": "SERVICE_ENV",
    # self.model will be send as 'MODEL'
    "model": "MODEL",
    # self.location will be send as 'LOCATION'
    "location": "LOCATION",
    # self.location will be send as 'LOCATION'
    # if any of above is set to none
    # 'location': None
    # then this value won't be set at all
}
DNSAAS_AUTO_UPDATE_HOST_DNS = bool_from_env("DNSAAS_AUTO_UPDATE_HOST_DNS")

DOMAIN_DATA_UPDATE_TOPIC = os.environ.get("DOMAIN_DATA_UPDATE_TOPIC", None)
DOMAIN_OWNER_TYPE = {
    "BO": "Business Owner",
    "TO": "Technical Owner",
}

# Transitions settings

# E.g.: pl (see: https://www.iso.org/iso-3166-country-codes.html)
CHANGE_HOSTNAME_ACTION_DEFAULT_COUNTRY = None


# Change management settings

CHANGE_MGMT_OPERATION_STATUSES = {
    "OPENED": os.getenv("CHANGE_MGMT_OPERATION_STATUS_OPENED", "Open"),
    "IN_PROGRESS": os.getenv("CHANGE_MGMT_OPERATION_STATUS_IN_PROGRESS", "In Progress"),
    "RESOLVED": os.getenv("CHANGE_MGMT_OPERATION_STATUS_RESOLVED", "Resolved"),
    "CLOSED": os.getenv("CHANGE_MGMT_OPERATION_STATUS_CLOSED", "Closed"),
    "REOPENED": os.getenv("CHANGE_MGMT_OPERATION_STATUS_REOPENED", "Reopened"),
    "TODO": os.getenv("CHANGE_MGMT_OPERATION_STATUS_TODO", "Todo"),
    "BLOCKED": os.getenv("CHANGE_MGMT_OPERATION_STATUS_BLOCKED", "Blocked"),
}

CHANGE_MGMT_BASE_OBJECT_LOADER = os.getenv("CHANGE_MGMT_BASE_OBJECT_LOADER", None)
CHANGE_MGMT_PROCESSOR = os.getenv(
    "CHANGE_MGMT_PROCESSOR", "ralph.operations.changemanagement.jira"
)

HERMES_CHANGE_MGMT_TOPICS = {
    "CHANGES": os.getenv(
        "HERMES_CHANGE_MGMT_CHANGES_TOPIC", "hermes.changemanagement.changes"
    )
}


# Hermes settings

ENABLE_HERMES_INTEGRATION = bool_from_env("ENABLE_HERMES_INTEGRATION")
HERMES = json.loads(os.environ.get("HERMES", "{}"))
HERMES["ENABLED"] = ENABLE_HERMES_INTEGRATION
# topic name where DC asset, cloud host, virtual server changes should be
# announced
HERMES_HOST_UPDATE_TOPIC_NAME = os.environ.get("HERMES_HOST_UPDATE_TOPIC_NAME", None)

HERMES_SERVICE_TOPICS = {
    "CREATE": os.environ.get(
        "SERVICE_CREATE_HERMES_TOPIC_NAME", "hermes.service.create"
    ),
    "DELETE": os.environ.get(
        "SERVICE_DELETE_HERMES_TOPIC_NAME", "hermes.service.delete"
    ),
    "UPDATE": os.environ.get(
        "SERVICE_UPDATE_HERMES_TOPIC_NAME", "hermes.service.update"
    ),
    "REFRESH": os.environ.get(
        "SERVICE_REFRESH_HERMES_TOPIC_NAME", "hermes.service.refresh"
    ),
}

if ENABLE_HERMES_INTEGRATION:
    INSTALLED_APPS += ("pyhermes.apps.django",)

ENABLE_SAVE_DESCENDANTS_DURING_NETWORK_SYNC = bool_from_env(
    "ENABLE_SAVE_DESCENDANTS_DURING_NETWORK_SYNC", True
)
ENABLE_EMAIL_NOTIFICATION = bool_from_env("ENABLE_EMAIL_NOTIFICATION")

EMAIL_HOST = os.environ.get("EMAIL_HOST", None)
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", None)
EMAIL_PORT = os.environ.get("EMAIL_PORT", 25)
EMAIL_USE_TLS = bool_from_env("EMAIL_USE_TLS", False)

EMAIL_FROM = os.environ.get("EMAIL_FROM", None)
EMAIL_MESSAGE_CONTACT_NAME = os.environ.get("EMAIL_MESSAGE_CONTACT_NAME", None)
EMAIL_MESSAGE_CONTACT_EMAIL = os.environ.get("EMAIL_MESSAGE_CONTACT_EMAIL", None)

SCM_TOOL_URL = os.getenv("SCM_TOOL_URL", "")

RALPH_HOST_URL = os.environ.get("RALPH_HOST_URL", None)

# METRICS
COLLECT_METRICS = False
ALLOW_PUSH_GRAPHS_DATA_TO_STATSD = False
STATSD_GRAPHS_PREFIX = "ralph.graphs"

ENABLE_REQUESTS_AND_QUERIES_METRICS = True
LARGE_NUMBER_OF_QUERIES_THRESHOLD = 25
LONG_QUERIES_THRESHOLD_MS = 250

TRANSITION_TEMPLATES = None

CONVERT_TO_DATACENTER_ASSET_DEFAULT_STATUS_ID = 1
CONVERT_TO_BACKOFFICE_ASSET_DEFAULT_STATUS_ID = 1

# Currency choices for django-money
DEFAULT_CURRENCY_CODE = "XXX"
CURRENCY_CHOICES = [
    (c.code, c.code) for i, c in CURRENCIES.items() if c.code != DEFAULT_CURRENCY_CODE
]
CURRENCY_CHOICES.append(("XXX", "---"))

OAUTH_CLIENT_ID = ""
OAUTH_SECRET = ""
OAUTH_TOKEN_URL = "https://localhost/"

GOOGLE_TAG_MANAGER_TAG_ID = os.environ.get("GOOGLE_TAG_MANAGER_TAG_ID", None)

ASSET_BUYOUT_CATEGORY_TO_MONTHS = json.loads(
    os.environ.get("ASSET_BUYOUT_CATEGORY_TO_MONTHS", "{}")
)

DATA_UPLOAD_MAX_NUMBER_FIELDS = 3000
