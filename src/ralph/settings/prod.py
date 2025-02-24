import json
import os

from ralph.settings import *  # noqa

DEBUG = bool_from_env("RALPH_DEBUG", False)

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"  # noqa

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.TokenAuthentication",
    # session authentication enabled for API requests from UI (ex. in
    # visualisation)
    "rest_framework.authentication.SessionAuthentication",
)

if os.environ.get("STORE_SESSIONS_IN_REDIS"):
    SESSION_ENGINE = "redis_sessions.session"
    if REDIS_SENTINEL_ENABLED:
        SESSION_REDIS_SENTINEL_LIST = REDIS_SENTINEL_HOSTS
        SESSION_REDIS_SENTINEL_MASTER_ALIAS = REDIS_CLUSTER_NAME
    else:
        SESSION_REDIS_HOST = REDIS_CONNECTION["HOST"]
        SESSION_REDIS_PORT = REDIS_CONNECTION["PORT"]
    SESSION_REDIS_DB = REDIS_CONNECTION["DB"]
    SESSION_REDIS_PASSWORD = REDIS_CONNECTION["PASSWORD"]
    SESSION_REDIS_PREFIX = "session"

if os.environ.get("USE_REDIS_CACHE"):
    DEFAULT_CACHE_OPTIONS = {
        "DB": os.environ.get("REDIS_CACHE_DB", REDIS_CONNECTION["DB"]),
        "PASSWORD": os.environ.get(
            "REDIS_CACHE_PASSWORD", REDIS_CONNECTION["PASSWORD"]
        ),
        "PARSER_CLASS": os.environ.get(
            "REDIS_CACHE_PARSER", "redis.connection.HiredisParser"
        ),
        "CONNECTION_POOL_CLASS": os.environ.get(
            "REDIS_CACHE_CONNECTION_POOL_CLASS", "redis.BlockingConnectionPool"
        ),
        "PICKLE_VERSION": -1,
    }

    CACHES = {
        "default": {
            "OPTIONS": (
                json.loads(
                    os.environ.get("REDIS_CACHE_OPTIONS", "{}")) or DEFAULT_CACHE_OPTIONS
            ),
        },
    }
    if REDIS_SENTINEL_ENABLED:
        CACHES["default"]["BACKEND"] = "ralph.lib.cache.DjangoConnectionPoolCache"  # noqa
    else:
        CACHES["default"]["BACKEND"] = "redis_cache.RedisCache"
        CACHES["default"]["LOCATION"] = json.loads(
            os.environ.get(
                "REDIS_CACHE_LOCATION",
                '"{}:{}"'.format(REDIS_CONNECTION["HOST"], REDIS_CONNECTION["PORT"]),
            )
        )

    if bool_from_env("RALPH_DISABLE_CACHE_FRAGMENTS", False):
        CACHES["template_fragments"] = {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }


if bool_from_env("COLLECT_METRICS"):
    COLLECT_METRICS = True
    STATSD_HOST = os.environ.get("STATSD_HOST")
    STATSD_PORT = os.environ.get("STATSD_PORT")
    STATSD_PREFIX = os.environ.get("STATSD_PREFIX")
    STATSD_MAXUDPSIZE = int(os.environ.get("STATSD_MAXUDPSIZE", 512))
    MIDDLEWARE = (
        "ralph.lib.metrics.middlewares.RequestMetricsMiddleware",
    ) + MIDDLEWARE

    ALLOW_PUSH_GRAPHS_DATA_TO_STATSD = bool_from_env("ALLOW_PUSH_GRAPHS_DATA_TO_STATSD")
    if ALLOW_PUSH_GRAPHS_DATA_TO_STATSD:
        STATSD_GRAPHS_PREFIX = os.environ.get("STATSD_GRAPHS_PREFIX", "ralph.graphs")

if bool_from_env('PROMETHEUS_METRICS_ENABLED', True):
    PROMETHEUS_METRICS_ENABLED = True
    PROMETHEUS_EXPORT_MIGRATIONS = False
    MIDDLEWARE = (
        'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ) + MIDDLEWARE
    MIDDLEWARE = MIDDLEWARE + (
        'django_prometheus.middleware.PrometheusAfterMiddleware',
    )
    INSTALLED_APPS += (
        'django_prometheus',
    )
