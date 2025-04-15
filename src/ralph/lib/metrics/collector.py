import logging
from contextlib import ContextDecorator

from django.conf import settings
from statsd import defaults, StatsClient

logger = logging.getLogger(__name__)
statsd = None

HOST = getattr(settings, "STATSD_HOST", defaults.HOST)
PORT = getattr(settings, "STATSD_PORT", defaults.PORT)
PREFIX = getattr(settings, "STATSD_PREFIX", defaults.PREFIX)
MAXUDPSIZE = getattr(settings, "STATSD_MAXUDPSIZE", defaults.MAXUDPSIZE)
IPV6 = getattr(settings, "STATSD_IPV6", defaults.IPV6)


def build_statsd_client(
    host=HOST, port=PORT, prefix=PREFIX, maxudpsize=MAXUDPSIZE, ipv6=IPV6
):
    return StatsClient(
        host=host, port=port, prefix=prefix, maxudpsize=maxudpsize, ipv6=ipv6
    )


if settings.COLLECT_METRICS and statsd is None:
    statsd = build_statsd_client()

if statsd is None:
    # mock statsd client to be able to use it without checking every time
    # if collecting metrics is enabled in settings (ex. when decorating a
    # function)
    class TimerMock(ContextDecorator):
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs):
            return False

        def start(self, *args, **kwargs):
            pass

        def stop(self, *args, **kwargs):
            pass

    class StatsdMockClient(object):
        def __init__(self, *args, **kwargs):
            logger.warning(
                "Statsd not installed or configured - metrics will NOT be collected"
            )

        def timer(self, *args, **kwargs):
            return TimerMock()

        def _mock(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return self._mock

    statsd = StatsdMockClient()
