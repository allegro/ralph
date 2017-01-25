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
    current_user = get_current_user()
    username = current_user.username if current_user else ''
    for data in obj.get_auto_txt_data():
        data['owner'] = username
        data['target_owner'] = settings.DNSAAS_OWNER
        publish_data.append(data)
    return publish_data


def _send_once(instance):
    publish_data_to_dnsaaas(instance)


if settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME:
    @pyhermes.publisher(
        topic=settings.DNSAAS_AUTO_TXT_RECORD_TOPIC_NAME,
        auto_publish_result=True
    )
    def publish_data_to_dnsaaas(obj):
        return _publish_data_to_dnsaaas(obj)

    # TODO(mkurek): consider changing it to `ralph.signals.post_commit`
    @receiver(post_save, sender=DataCenterAsset)
    def post_save_dc_asset(sender, instance, **kwargs):
        _send_once(instance)

    @receiver(post_save, sender=Cluster)
    def post_save_cluster(sender, instance, **kwargs):
        _send_once(instance)

    @receiver(post_save, sender=VirtualServer)
    def post_save_virtual_server(sender, instance, **kwargs):
        _send_once(instance)
