import time

from django.conf import settings
from redis import Redis
from rq import Queue

from .conf import get_redis_connection_params

redis_conn = Redis(**get_redis_connection_params())


RALPH_EXTERNAL_SERVICES = getattr(settings, 'RALPH_EXTERNAL_SERVICES', {})


class QueuedServiceError(Exception):
    pass


class ExternalService(object):
    def __init__(self, service_name):
        """Initializing queue and check existence of service."""
        service = RALPH_EXTERNAL_SERVICES.get(service_name.upper())
        if not service:
            raise ValueError('The {} service doesn\'t exist'.format(service))
        self.method = service['method']
        self.queue = Queue(
            name=service['name'], connection=redis_conn, async=True
        )

    def run(self, **kwargs):
        """Run function with params on external service.

        Basically this method call external method with params wich it
        accept. You must now about accepted params by external function
        and provide it.

        Args:
            kwargs: A dictonary with params.

        Returns:
            Returns external function result - type of result depends of
            external method.

        Raises:
            QueuedServiceError: If something goes wrong on queue.
        """
        job = self.queue.enqueue(self.method, **kwargs)
        if not job.is_queued:
            raise QueuedServiceError
        while job and not any([job.is_finished, job.is_failed]):
            time.sleep(0.1)
        return job.result
