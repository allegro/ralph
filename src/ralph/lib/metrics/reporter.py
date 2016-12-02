import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class MetricsReporter(object):
    """
    Context manager for short-living processes, which have no accesss to
    global metrology reporter (for example are running in forked process) and/or
    exits using `os._exit`.

    This context manager provides starting metrology reporter when entering it
    and sending metrics when exiting.

    Example:

    with MetricsReporter():
        <do some task here>
    """
    def __init__(self):
        self.reporter = None

    def __enter__(self):
        self._start_metrics_reporter()

    def __exit__(self, exc, exv, trace):
        self._stop_reporter()

    def _start_metrics_reporter(self):
        """
        Enable metrology reporter in job process (threads are not "inherited"
        when forking).
        """
        if settings.COLLECT_METRICS:
            self.reporter = settings.GET_REPORTER()
            if self.reporter:
                logger.debug('Starting metrics reporter on worker')
                self.reporter.start()
            else:
                logger.warning(
                    'Reporter not started - GET_REPOTER method returned None'
                )

    def _stop_reporter(self):
        # `atexit` (which is used by metrology) is not called when `os._exit`
        # is used (which is used by RQ to exit from forked process)
        if self.reporter:
            logger.debug('Stopping reporter')
            self.reporter._exit()
