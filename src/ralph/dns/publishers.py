# -*- coding: utf-8 -*-
import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from threadlocals.threadlocals import get_current_user

from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import Cluster
from ralph.virtual.models import VirtualServer


def _publish_data_to_dnsaaas(obj):
    publish_data = []
    for data in obj.get_auto_txt_data():
        data['owner'] = settings.DNSAAS_OWNER
        #TODO::
        #data['target_owner'] = get_current_user().username
        publish_data.append(data)
    return publish_data


@pyhermes.publisher(
    topic=settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME,
    auto_publish_result=True
)
def publish_data_to_dnsaaas(obj):
    return _publish_data_to_dnsaaas(obj)


@receiver(post_save, sender=DataCenterAsset)
def post_save_dc_asset(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)


@receiver(post_save, sender=Cluster)
def post_save_cluster(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)


@receiver(post_save, sender=VirtualServer)
def post_save_virtual_server(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)
