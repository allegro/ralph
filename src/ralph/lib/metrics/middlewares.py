import logging
import time

from django.conf import settings
from django.utils.text import slugify
from metrology import Metrology

PROCESSING_TIME_METRIC_PREFIX = getattr(
    settings, 'PROCESSING_TIME_METRIC_PREFIX', 'processing_time'
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
    Middleware reporting request metrics (such as processing time) to metrology

    How to use it:
    * add this middleware at the beginning of MIDDLEWARE_CLASSES in your
      settings
    * define and start Metrology reporter in you Django settings (more details
      here: https://metrology.readthedocs.io/en/latest/)
    """

    def process_request(self, request):
        request._request_start_time = time.monotonic()

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
            (time.monotonic() - request._request_start_time) * 1000
        )
        logger.info(
            'Processing time [ms]: {}'.format(processing_time),
            extra=dict(processing_time=processing_time, **common_log_params)
        )
        processing_timer = Metrology.timer(processing_time_metric_name)
        processing_timer.update(processing_time)  # in miliseconds

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
