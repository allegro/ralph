import logging
from contextlib import ContextDecorator

from django.conf import settings

logger = logging.getLogger(__name__)
statsd = None

if settings.COLLECT_METRICS:
    try:
        from statsd.defaults.django import statsd
    except ImportError:  # statsd not installed
        pass

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
                'Statsd not installed or configured - metrics will NOT be '
                'collected'
            )

        def timer(self, *args, **kwargs):
            return TimerMock()

        def _mock(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return self._mock

    statsd = StatsdMockClient()
