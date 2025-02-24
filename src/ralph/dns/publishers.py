# -*- coding: utf-8 -*-
import logging

import pyhermes
from django.conf import settings
from pyhermes import publish

from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import Cluster
from ralph.signals import post_commit
from ralph.virtual.models import VirtualServer

logger = logging.getLogger(__name__)


def _get_txt_data_to_publish_to_dnsaas(obj):
    publish_data = []
    for data in obj.get_auto_txt_data():
        data["owner"] = settings.DNSAAS_OWNER
        data["target_owner"] = settings.DNSAAS_OWNER
        publish_data.append(data)
    return publish_data


@pyhermes.publisher(
    topic=settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME or "",
    # call publish directly to make testing (overriding settings) easier
    auto_publish_result=False,
)
def publish_data_to_dnsaaas(obj):
    if settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME:
        logger.info("Publishing DNS TXT records update for {}".format(obj))
        publish(
            settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME,
            _get_txt_data_to_publish_to_dnsaas(obj),
        )


post_commit(publish_data_to_dnsaaas, DataCenterAsset)
post_commit(publish_data_to_dnsaaas, Cluster)
post_commit(publish_data_to_dnsaaas, VirtualServer)
