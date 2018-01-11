import logging

from django.conf import settings
from django.db import connections
from redis import StrictRedis
from rest_framework import renderers
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# StrictRedis will maintain connection (pool) and re-establish them
# if disconnected (ex. socket was closed).
strict_redis = StrictRedis(
    host=settings.REDIS_CONNECTION['HOST'],
    port=settings.REDIS_CONNECTION['PORT'],
    db=settings.REDIS_CONNECTION['DB'],
    password=settings.REDIS_CONNECTION['PASSWORD'],
    socket_timeout=settings.REDIS_CONNECTION['TIMEOUT'],
    socket_connect_timeout=settings.REDIS_CONNECTION['CONNECT_TIMEOUT'],
)


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, str):
            data = data.encode(self.charset)
        else:
            data = str(data)
        return data


def _test_redis_conn():
    strict_redis.ping()


def _test_db_conn():
    connections['default'].cursor()


def _perform_all_health_checks():
    messages = []
    for health_check_func in [_test_db_conn, _test_redis_conn]:
        try:
            health_check_func()
        except Exception as e:
            msg = 'Health check failed. Function: {}, exception: {}'.format(
                health_check_func.__name__, e
            )
            logger.critical(
                msg,
                extra={
                    'action_type': 'HEALTH_CHECK',
                    'error': str(e)
                }
            )
            messages.append(msg)
    return messages


@api_view(['GET'])
@permission_classes((AllowAny,))
@renderer_classes((PlainTextRenderer,))
def status_ping(request):
    return Response('pong')


@api_view(['GET'])
@permission_classes((AllowAny,))
@renderer_classes((PlainTextRenderer,))
def status_health(request):
    health_checks_errors = _perform_all_health_checks()
    if not health_checks_errors:
        return Response('Healthy')
    else:
        response = 'Not Healthy\n' + "\n".join(health_checks_errors)
        return Response(response, status=503)
