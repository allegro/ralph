# -*- coding: utf-8 -*-
import pyhermes
from django.conf import settings


def _get_host_data(instance):
    from ralph.assets.api.serializers import DCHostSerializer
    serializer = DCHostSerializer(instance=instance)
    return serializer.data

if settings.HERMES_HOST_UPDATE_TOPIC_NAME:
    @pyhermes.publisher(
        topic=settings.HERMES_HOST_UPDATE_TOPIC_NAME, auto_publish_result=True
    )
    def publish_host_update(instance):
        return _get_host_data(instance)
