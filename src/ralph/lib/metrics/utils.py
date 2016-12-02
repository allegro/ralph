import logging

from django.conf import settings
from metrology import Metrology

logger = logging.getLogger(__name__)


def mark(metric_name):
    """
    Mark event in metrics collector.
    """
    if settings.COLLECT_METRICS:
        logger.info('New mark event: {}'.format(metric_name), extra={
            'metric_name': metric_name
        })
        counter = Metrology.meter(metric_name)
        counter.mark()
