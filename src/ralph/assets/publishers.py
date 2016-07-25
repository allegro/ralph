# -*- coding: utf-8 -*-
import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import Cluster
from ralph.virtual.models import VirtualServer


#TODO:: change topic name, shouldn't this be full path or from settings?
@pyhermes.publisher(topic='auto_txt_record', auto_publish_result=True)
def publish_data_to_dnsaaas(obj):
    return obj.publish_data


@receiver(post_save, sender=DataCenterAsset)
def post_save_dc_asset(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)


@receiver(post_save, sender=Cluster)
def post_save_cluster(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)


@receiver(post_save, sender=VirtualServer)
def post_save_virtual_server(sender, instance, **kwargs):
    publish_data_to_dnsaaas(instance)
