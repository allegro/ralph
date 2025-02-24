import logging

logger = logging.getLogger(__name__)


def endpoint(cloud_provider, event_data):
    """The endpoint for DC asset synchronisation that does nothing."""
    logger.info("Received new DC asset synchronisation event. Doing nothing.")
