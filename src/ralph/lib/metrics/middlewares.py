import logging
import time

from django.conf import settings

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

logger = logging.getLogger(__name__)


class RequestMetricsMiddleware(object):
    """
    Middleware reporting request metrics (such as processing time) to statsd

    How to use it:
    * add this middleware at the beginning of MIDDLEWARE_CLASSES in your
      settings
    * configure statsd in your settings:
      http://statsd.readthedocs.io/en/v3.2.1/configure.html#in-django
    """

    def process_request(self, request):
        request._request_start_time = time.monotonic()

    def _collect_metrics(self, request, response):
        try:
            url_name = request.resolver_match.url_name
        except AttributeError:
            logger.warning(
                'URL resolver not found', extra={'path': request.path}
            )
            url_name = UNKNOWN_URL_NAME

        common_log_params = {
            'request_method': request.method,
            'url_name': url_name,
            'status_code': response.status_code,
        }

        # processing time
        processing_time_metric_name = METRIC_NAME_TMPL.format(
            prefix=PROCESSING_TIME_METRIC_PREFIX, **common_log_params
        )
        processing_time_all_urls_metric_name = ALL_URLS_METRIC_NAME_TMPL.format(
            prefix=PROCESSING_TIME_METRIC_PREFIX, **common_log_params
        )
        processing_time = int(
            (time.monotonic() - request._request_start_time) * 1000
        )
        statsd.timing(processing_time_metric_name, processing_time)
        statsd.timing(processing_time_all_urls_metric_name, processing_time)

        # requests counter
        requests_counter_metric_name = METRIC_NAME_TMPL.format(
            prefix=REQUESTS_COUNTER_METRIC_PREFIX, **common_log_params
        )
        statsd.incr(requests_counter_metric_name)

    def process_response(self, request, response):
        try:
            self._collect_metrics(request, response)
        except Exception:
            logger.exception('Exception during collecting metrics')
        return response
