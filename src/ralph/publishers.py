# -*- coding: utf-8 -*-
import pyhermes
from django.conf import settings


if settings.HERMES_HOST_UPDATE_TOPIC_NAME:
    @pyhermes.publisher(
        topic=settings.HERMES_HOST_UPDATE_TOPIC_NAME, auto_publish_result=True
    )
    def publish_host_update(data):
        return data
