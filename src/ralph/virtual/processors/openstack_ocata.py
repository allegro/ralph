import logging

from ralph.virtual.models import CloudHost


logger = logging.getLogger(__name__)


def endpoint(cloud_provider, event_data):
    try:
        event_type = event_data['event_type']
        event_payload = event_data['payload']

        logger.info(
            'Received {} event from {}'.format(event_type, cloud_provider.name)
        )

        if event_type not in OS_EVENT_HANDLERS:
            logger.debug('Event type does not have specified handler.')

        handler = OS_EVENT_HANDLERS[event_type]
        handler(event_payload)
    except KeyError as e:
        logger.error('Malformed event payload. Key {} not found'.format(e))


def delete_cloudhost(event_payload):
    instance_uuid = event_payload['nova_object.data']['uuid']
    CloudHost.objects.filter(host_id=instance_uuid).delete()


OS_EVENT_HANDLERS = {
    'instance.delete.end': delete_cloudhost
}
