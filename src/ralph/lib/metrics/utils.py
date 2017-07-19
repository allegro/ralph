import logging

from .collector import statsd

logger = logging.getLogger(__name__)


# deprecated - use statsd explicitly
def mark(metric_name):
    """
    Mark event in metrics collector.
    """
    statsd.incr(metric_name)
