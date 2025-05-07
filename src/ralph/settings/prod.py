from ralph.settings import *  # noqa
import os
from ralph.settings import (
    REDIS_CONNECTION,
    INSTALLED_APPS,
    MIDDLEWARE,
    bool_from_env,
    REDIS_SENTINEL_ENABLED,
    REDIS_SENTINEL_HOSTS,
    REDIS_CLUSTER_NAME,
    REST_FRAMEWORK,
)

DEBUG = bool_from_env("RALPH_DEBUG", False)

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"  # noqa

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.TokenAuthentication",
    # session authentication enabled for API requests from UI (ex. in
    # visualisation)
    "rest_framework.authentication.SessionAuthentication",
)

if os.environ.get("STORE_SESSIONS_IN_REDIS"):
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"

if os.environ.get("USE_REDIS_CACHE"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ.get(
                "REDIS_CACHE_LOCATION",
                f"redis://{REDIS_CLUSTER_NAME}/{os.environ.get('REDIS_CACHE_DB', REDIS_CONNECTION['DB'])}",
            ),
            "OPTIONS": {
                "DB": os.environ.get("REDIS_CACHE_DB", REDIS_CONNECTION["DB"]),
                "PASSWORD": os.environ.get(
                    "REDIS_CACHE_PASSWORD", REDIS_CONNECTION["PASSWORD"]
                ),
                "PARSER_CLASS": os.environ.get(
                    "REDIS_CACHE_PARSER", "redis.connection.HiredisParser"
                ),
                "PICKLE_VERSION": -1,
                "CLIENT_CLASS": "django_redis.client.DefaultClient"
                if not REDIS_SENTINEL_ENABLED
                else "django_redis.client.SentinelClient",
                "SENTINELS": REDIS_SENTINEL_HOSTS or [],
            },
        },
    }

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

if bool_from_env("PROMETHEUS_METRICS_ENABLED", True):
    PROMETHEUS_METRICS_ENABLED = True
    PROMETHEUS_EXPORT_MIGRATIONS = False
    MIDDLEWARE = (
        "django_prometheus.middleware.PrometheusBeforeMiddleware",
    ) + MIDDLEWARE
    MIDDLEWARE = MIDDLEWARE + (
        "django_prometheus.middleware.PrometheusAfterMiddleware",
    )
    INSTALLED_APPS += ("django_prometheus",)
