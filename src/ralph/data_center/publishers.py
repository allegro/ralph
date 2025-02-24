# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

import pyhermes
from django.conf import settings
from pyhermes.publishing import publish

logger = logging.getLogger(__name__)


def _get_host_data(instance):
    from ralph.assets.api.serializers_dchosts import (
        DCHostPhysicalSerializer,
        DCHostSerializer,
    )
    from ralph.data_center.models import DataCenterAsset

    if isinstance(instance, DataCenterAsset):
        serializer = DCHostPhysicalSerializer(instance=instance)
    else:
        serializer = DCHostSerializer(instance=instance)
    if hasattr(serializer.instance, "_previous_state"):
        data = deepcopy(serializer.data)
        data["_previous_state"] = {
            k: v
            for k, v in serializer.instance._previous_state.items()
            if k in serializer.instance.previous_dc_host_update_fields
        }
    else:
        data = serializer.data
    return data


@pyhermes.publisher(
    topic=settings.HERMES_HOST_UPDATE_TOPIC_NAME or "", auto_publish_result=False
)
def publish_host_update(instance):
    """
    Publish information about DC Host updates using DCHost API serializer.
    """
    if settings.HERMES_HOST_UPDATE_TOPIC_NAME:
        logger.info(
            "Publishing host update for {}".format(instance),
            extra={
                "type": "PUBLISH_HOST_UPDATE",
                "instance_id": instance.id,
                "content_type": instance.content_type.name,
            },
        )
        host_data = _get_host_data(instance)
        # call publish directly to make testing easier
        logger.info(
            "Publishing DCHost update",
            extra={
                "publish_data": host_data,
            },
        )
        publish(settings.HERMES_HOST_UPDATE_TOPIC_NAME, host_data)


def publish_host_update_from_related_model(instance, field_path):
    from ralph.data_center.models import DCHost

    updated_instances = DCHost.objects.filter(**{field_path: instance})
    logger.info(
        "Publishing host update for {} instances".format(updated_instances.count())
    )
    for instance in updated_instances:
        publish_host_update(instance)
