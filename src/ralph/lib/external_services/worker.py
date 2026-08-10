from django.db import connection
from rq import SimpleWorker, Worker


class _CloseObsoleteConnectionsMixin:
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

        This comes in pair with `CONN_MAX_AGE` settings
        (https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-CONN_MAX_AGE)
        To properly handle closing connection when using persistent connections
        to the database, it's value should be lower than wait timeout of the
        database server.

        Resources:
        * https://github.com/translate/pootle/issues/4094
        * http://dev.mysql.com/doc/refman/5.7/en/gone-away.html
        * https://dev.mysql.com/doc/refman/5.7/en/error-lost-connection.html
        * http://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#sysvar_wait_timeout
        """
        connection.close_if_unusable_or_obsolete()
        result = super().perform_job(*args, **kwargs)
        connection.close_if_unusable_or_obsolete()
        return result


class RalphWorker(_CloseObsoleteConnectionsMixin, Worker):
    """
    Worker for Ralph jobs on RQ.

    Use it in management command using `--worker-class` param, for example:
    ```
    ralph rqworker --worker-class=ralph.lib.external_services.worker.RalphWorker default
    ```
    """


class RalphSimpleWorker(_CloseObsoleteConnectionsMixin, SimpleWorker):
    """
    Non-forking Ralph worker (runs jobs in the worker process).

    Use it for jobs that spawn threads (e.g. the switchport netmaker refresh)
    and on platforms where forking a work-horse is problematic - notably macOS,
    where ``fork()`` after Objective-C initialization crashes the child with
    ``+[... initialize] may have been in progress in another thread when
    fork() was called``.
    ```
    ralph rqworker --worker-class=ralph.lib.external_services.worker.RalphSimpleWorker ralph_switchports
    ```
    """  # noqa
