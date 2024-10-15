import logging

from django.conf import settings
from django.db import connections
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from ralph.lib.redis import get_redis_connection

logger = logging.getLogger(__name__)

# StrictRedis will maintain connection (pool) and re-establish them
# if disconnected (ex. socket was closed).
strict_redis = get_redis_connection(settings.REDIS_CONNECTION)


def _test_redis_conn():
    strict_redis.ping()


def _test_db_conn():
    connections["default"].cursor()


def _perform_all_health_checks():
    messages = []
    for health_check_func in [_test_db_conn, _test_redis_conn]:
        try:
            health_check_func()
        except Exception as e:
            msg = "Health check failed. Function: {}, exception: {}".format(
                health_check_func.__name__, e
            )
            logger.critical(msg, extra={"action_type": "HEALTH_CHECK", "error": str(e)})
            messages.append(msg)
    return messages


@require_GET
def status_ping(request):
    return HttpResponse("pong", content_type="text/plain")


@require_GET
def status_health(request):
    health_checks_errors = _perform_all_health_checks()
    if not health_checks_errors:
        return HttpResponse("Healthy", content_type="text/plain")
    else:
        response = "Not Healthy\n" + "\n".join(health_checks_errors)
        return HttpResponse(response, status=503, content_type="text/plain")
