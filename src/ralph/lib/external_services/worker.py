import logging
from django.conf import settings
from django.db import connection
from rq import Worker

logger = logging.getLogger(__name__)


class RalphWorker(Worker):
    """
    Worker for Ralph jobs on RQ.

    Use it in management command using `--worker-class` param, for example:
    ```
    ralph rqworker --worker-class=ralph.lib.external_services.worker.RalphWorker default  # noqa
    ```
    """
    def perform_job(self, *args, **kwargs):
        """
        Handles connection (wait) timeouts on RQ.

        If idle time of the worker exceeds wait timeout for connection to the
        database (for MySQL it's 8 hours by default), connection is closed by
        database server, but Django still thinks it has open connection to the
        DB. This ends with errors like 'Lost connection to MySQL server' or
        'MySQL server has gone away' (or similar for other backends).

        Solution below fixes this bug by closing connections before and after
        each job on worker and forcing Django to open a new one.

        This comes in pair with `CONN_MAX_AGE` settings (https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-CONN_MAX_AGE).  # noqa
        To properly handle closing connection when using persistent connections
        to the database, it's value should be lower than wait timeout of the
        database server.

        Resources:
        * https://github.com/translate/pootle/issues/4094
        * http://dev.mysql.com/doc/refman/5.7/en/gone-away.html
        * https://dev.mysql.com/doc/refman/5.7/en/error-lost-connection.html
        * http://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#sysvar_wait_timeout  # noqa
        """
        reporter = self._start_metrics_reporter()
        connection.close_if_unusable_or_obsolete()
        result = super().perform_job(*args, **kwargs)
        connection.close_if_unusable_or_obsolete()
        self._send_metrics(reporter)
        return result

    def _start_metrics_reporter(self):
        """
        Enable metrology reporter in job process (threads are not "inherited"
        when forking).
        """
        if settings.MEASURE_JOBS_STATS:
            reporter = settings.GET_REPORTER()
            if reporter:
                logger.debug('Starting metrics reporter on worker')
                reporter.start()
                return reporter

    def _send_metrics(self, reporter):
        # atexit (which is used by metrology) is not called when os._exit
        # is used (which is used by RQ to exit from forked process)
        if reporter:
            reporter._exit()
