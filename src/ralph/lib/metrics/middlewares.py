import functools
import logging
import threading
import time
from collections import deque
from resource import getrusage, RUSAGE_SELF

from django.conf import settings
from django.db.backends.utils import CursorWrapper
from django.utils.deprecation import MiddlewareMixin

from .collector import statsd

PROCESSING_TIME_METRIC_PREFIX = getattr(
    settings, 'PROCESSING_TIME_METRIC_PREFIX', 'processing_time'
)
REQUESTS_COUNTER_METRIC_PREFIX = getattr(
    settings, 'REQUESTS_COUNTER_METRIC_PREFIX', 'requests_count'
)

METRIC_NAME_TMPL = getattr(
    settings,
    'REQUESTS_METRIC_NAME_TMPL',
    '{prefix}.{url_name}.{request_method}.{status_code}'
)
ALL_URLS_METRIC_NAME_TMPL = getattr(
    settings,
    'REQUESTS_ALL_URLS_METRIC_NAME_TMPL',
    '{prefix}_all_urls.{request_method}'
)
UNKNOWN_URL_NAME = 'unknown'

REQUESTS_METRICS_ENABLED = getattr(
    settings,
    'ENABLE_REQUESTS_AND_QUERIES_METRICS',
    True
)
LARGE_NUMBER_OF_QUERIES_THRESHOLD = getattr(
    settings,
    'LARGE_NUMBER_OF_QUERIES_THRESHOLD',
    25
)
LONG_QUERIES_THRESHOLD_MS = getattr(
    settings,
    'LONG_QUERIES_THRESHOLD_MS',
    250
)

logger = logging.getLogger(__name__)

queries_data = threading.local()
old_execute = CursorWrapper.execute
old_executemany = CursorWrapper.executemany


class QueryLogEntry:
    sql: str  # noqa
    duration: float  # noqa

    def __init__(self, sql: str, duration: float):
        self.sql = sql,
        self.duration = duration

    def __str__(self):
        return "'{}' took {} ms".format(self.sql, self.duration * 1000)


def get_queries_log() -> deque:
    if not hasattr(queries_data, 'queries'):
        queries_data.queries = deque(maxlen=9000)
    return queries_data.queries


def add_query_log(duration: float, sql: str) -> None:
    get_queries_log().append(QueryLogEntry(sql=sql, duration=duration))


@functools.wraps(old_execute)
def new_execute(self, sql, params=None):  # type: ignore
    """
    Wraps original cursor execute method and adds thread safe timing to it.
    """
    start = time.monotonic()
    try:
        return old_execute(self, sql, params)
    finally:
        duration = time.monotonic() - start
        add_query_log(sql=sql, duration=duration)


@functools.wraps(old_executemany)
def new_executemany(self, sql, param_list):  # type: ignore
    """
    Wraps original cursor executemany method and adds thread safe timing to it.
    """
    start = time.monotonic()
    try:
        return old_executemany(self, sql, param_list)
    finally:
        duration = time.monotonic() - start
        add_query_log(sql=sql, duration=duration)


# Monkey patch
def patch_cursor() -> None:
    CursorWrapper.execute = new_execute
    CursorWrapper.executemany = new_executemany


def get_per_query_stat(query_stats):
    return "\n".join(str(stat) for stat in query_stats)


class RequestMetricsMiddleware(MiddlewareMixin):
    """
    Middleware reporting request metrics (such as processing time) to statsd

    How to use it:
    * add this middleware at the beginning of MIDDLEWARE in your
      settings
    * configure statsd in your settings:
      http://statsd.readthedocs.io/en/v3.2.1/configure.html#in-django
    """

    IGNORED_PATHS = (
        'javascript-catalog',
        'microservice_contract-health',
        'microservice_contract-ping',
        'microservice_contract-ping-service-id',
        'microservice_contract-info',
        'microservice_public_endpoints',
    )

    def process_request(self, request):
        request._request_start_time = time.monotonic()
        request._start_resources = getrusage(RUSAGE_SELF)
        get_queries_log().clear()

    def _collect_metrics(self, request, response):
        if not REQUESTS_METRICS_ENABLED:
            return
        if not request.resolver_match:
            return

        try:
            url_name = request.resolver_match.url_name
        except AttributeError:
            logger.warning(
                'URL resolver not found', extra={'path': request.path}
            )
            url_name = UNKNOWN_URL_NAME

        view_name = request.resolver_match.view_name
        if view_name in self.IGNORED_PATHS:
            return

        common_log_params = {
            'request_method': request.method,
            'url_name': url_name,
            'status_code': response.status_code,
        }

        query_stats = get_queries_log()

        # processing time
        end_resources, end_time = getrusage(RUSAGE_SELF), time.monotonic()
        real_time = (end_time - request._request_start_time) * 1000
        sys_time = (end_resources.ru_stime - request._start_resources.ru_stime) * 1000  # noqa
        user_time = (end_resources.ru_utime - request._start_resources.ru_utime) * 1000  # noqa
        cpu_time = sys_time + user_time
        queries_time = sum(stat.duration for stat in query_stats) * 1000

        processing_time_metric_name = METRIC_NAME_TMPL.format(
            prefix=PROCESSING_TIME_METRIC_PREFIX, **common_log_params
        )
        processing_time_all_urls_metric_name = ALL_URLS_METRIC_NAME_TMPL.format(
            prefix=PROCESSING_TIME_METRIC_PREFIX, **common_log_params
        )
        processing_time = int(real_time)
        statsd.timing(processing_time_metric_name, processing_time)
        statsd.timing(processing_time_all_urls_metric_name, processing_time)

        # requests counter
        requests_counter_metric_name = METRIC_NAME_TMPL.format(
            prefix=REQUESTS_COUNTER_METRIC_PREFIX, **common_log_params
        )
        statsd.incr(requests_counter_metric_name)

        queries_count = len(query_stats)

        data = {
            'queries_time': queries_time,
            'queries_count': queries_count,
            'real_time': real_time,
            'sys_time': sys_time,
            'user_time': user_time,
            'cpu_time': cpu_time,
            'cpu_real_ratio': cpu_time / real_time * 100,
            'queries_real_ratio': queries_time / real_time * 100,
        }
        metadata = {
            'path': request.get_full_path(),
            'url_name': url_name,
            'view_name': view_name,
            'method': request.method,
            'http_user_agent': request.META.get('HTTP_USER_AGENT'),
            'username': request.user.username,
        }

        logger.info(
            'Request time:\n'
            '\treal: {real_time}\n'
            '\tsys: {sys_time}\n'
            '\tuser: {user_time}\n'
            '\ttotal CPU time: {cpu_time}\n'
            '\tCPU to real time ratio: {cpu_real_ratio}\n'

            'Queries:\n'
            '\tcount: {queries_count}\n'
            '\ttotal time: {queries_time}\n'
            '\tqueries time to real time ratio: {queries_real_ratio}'.format(
                **data
            ), extra={
                **data,
                **metadata
            }
        )

        if queries_count > LARGE_NUMBER_OF_QUERIES_THRESHOLD:
            logger.warning("A lot of queries ({}) in {}: {}".format(
                queries_count, view_name, get_per_query_stat(query_stats)),
                extra={**metadata}
            )
        elif queries_time > LONG_QUERIES_THRESHOLD_MS:
            logger.warning("Long queries (total of {} ms) in {}: {}".format(
                queries_time, view_name, get_per_query_stat(query_stats)),
                extra={**metadata}
            )

    def process_response(self, request, response):
        try:
            self._collect_metrics(request, response)
        except Exception:
            logger.exception('Exception during collecting metrics')
        return response
