import time

import django_rq
from django.conf import settings


class QueuedServiceError(Exception):
    pass


class ExternalService(object):
    services = settings.RALPH_EXTERNAL_SERVICES

    def __init__(self, service_name):
        """Initializing queue and check existence of service."""
        service = self.services.get(service_name.upper())
        if not service:
            raise ValueError('The {} service doesn\'t exist'.format(service))
        self.method = service['method']
        self.queue = django_rq.get_queue(service['queue_name'])

    def run(self, **kwargs):
        """Run function with params on external service.

        Basically this method call external method with params which it
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

    def run_async(self, **kwargs):
        job = self.queue.enqueue(self.method, kwargs=kwargs)
        return job


class InternalService(ExternalService):
    """
    Service with DB (and Ralph-code) access
    """
    services = settings.RALPH_INTERNAL_SERVICES
