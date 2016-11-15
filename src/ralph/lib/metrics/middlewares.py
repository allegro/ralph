import logging
import time

from django.conf import settings
from django.db import connection
from django.utils.text import slugify
from metrology import Metrology

PROCESSING_TIME_METRIC_PREFIX = getattr(
    settings, 'PROCESSING_TIME_METRIC_PREFIX', 'processing_time'
)
DB_QUERIES_COUNT_METRIC_PREFIX = getattr(
    settings, 'DB_QUERIES_COUNT_METRIC_PREFIX', 'db_queries_count'
)
DB_QUERIES_TIME_METRIC_PREFIX = getattr(
    settings, 'DB_QUERIES_TIME_METRIC_PREFIX', 'db_queries_time'
)
REQUESTS_COUNTER_METRIC_PREFIX = getattr(
    settings, 'REQUESTS_COUNTER_METRIC_PREFIX', 'requests_count'
)

METRIC_NAME_TMPL = getattr(
    settings,
    'METRIC_NAME_TMPL',
    '{prefix}.{url_name}.{request_method}.{status_code}'
)

logger = logging.getLogger(__name__)


class RequestMetricsMiddleware(object):
    """
    Middleware reporting request metrics (such as processing time, database
    queries count) to metrology.

    How to use it:
    * add this middleware at the beginning of MIDDLEWARE_CLASSES in your
      settings
    * define and start Metrology reporter in you Django settings (more details
      here: https://metrology.readthedocs.io/en/latest/)
    """

    def process_request(self, request):
        request._request_start_time = time.time()

    def _collect_metrics(self, request, response):
        try:
            url_name = request.resolver_match.url_name
        except AttributeError:
            url_name = slugify(request.path)

        common_log_params = {
            'request_method': request.method,
            'url_name': url_name,
            'status_code': response.status_code,
        }

        # processing time
        processing_time_metric_name = METRIC_NAME_TMPL.format(
            prefix=PROCESSING_TIME_METRIC_PREFIX, **common_log_params
        )
        processing_time = int(
            (time.time() - request._request_start_time) * 1000
        )
        logger.info('Processing time [ms]: {}'.format(processing_time), extra={
            'processing_time': processing_time, **common_log_params
        })
        processing_timer = Metrology.timer(processing_time_metric_name)
        processing_timer.update(processing_time)  # in miliseconds

        # database queries count and time
        queries_time = 0.0  # in miliseconds
        queries_count = 0
        for q in connection.queries:
            queries_time += float(q.get('time', 0.0)) * 1000
            queries_count += 1

        logger.info('DB queries count: {}'.format(queries_count), extra={
            'db_queries_count': queries_count, **common_log_params
        })
        db_queries_count_metric_name = METRIC_NAME_TMPL.format(
            prefix=DB_QUERIES_COUNT_METRIC_PREFIX, **common_log_params
        )
        db_queries_counter = Metrology.meter(db_queries_count_metric_name)
        db_queries_counter.mark(value=queries_count)

        logger.info('DB queries time [ms]: {}'.format(queries_time), extra={
            'db_queries_time': queries_time, **common_log_params
        })
        db_queries_time_metric_name = METRIC_NAME_TMPL.format(
            prefix=DB_QUERIES_TIME_METRIC_PREFIX, **common_log_params
        )
        db_queries_timer = Metrology.timer(db_queries_time_metric_name)
        db_queries_timer.update(int(queries_time))

        # requests counter
        requests_counter_metric_name = METRIC_NAME_TMPL.format(
            prefix=REQUESTS_COUNTER_METRIC_PREFIX, **common_log_params
        )
        requests_counter = Metrology.meter(requests_counter_metric_name)
        requests_counter.mark()

    def process_response(self, request, response):
        try:
            self._collect_metrics(request, response)
        except Exception:
            logger.exception('Exception during collecting metrics')
        return response
