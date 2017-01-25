# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

import pyhermes
from django.conf import settings
from pyhermes.publishing import publish

logger = logging.getLogger(__name__)


def _get_host_data(instance):
    from ralph.assets.api.serializers import DCHostSerializer
    serializer = DCHostSerializer(instance=instance)
    if hasattr(serializer.instance, '_previous_state'):
        data = deepcopy(serializer.data)
        data['_previous_state'] = {
            k: v for k, v in serializer.instance._previous_state.items()
            if k in serializer.instance.previous_dc_host_update_fields
        }
    else:
        data = serializer.data
    return data


@pyhermes.publisher(
    topic=settings.HERMES_HOST_UPDATE_TOPIC_NAME or '',
    auto_publish_result=False
)
def publish_host_update(instance):
    """
    Publish information about DC Host updates using DCHost API serializer.
    """
    if settings.HERMES_HOST_UPDATE_TOPIC_NAME:
        logger.info(
            'Publishing host update for {}'.format(instance),
            extra={
                'type': 'PUBLISH_HOST_UPDATE',
                'instance_id': instance.id,
                'content_type': instance.content_type.name,
            }
        )
        host_data = _get_host_data(instance)
        # call publish directly to make testing easier
        publish(settings.HERMES_HOST_UPDATE_TOPIC_NAME, host_data)
