# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ipaddress

from django.db import migrations, models


def move_to_networks(apps, schema_editor):
    DataCenterAsset = apps.get_model('data_center', 'DataCenterAsset')
    IPAddress = apps.get_model('networks', 'IPAddress')
    assets = DataCenterAsset.objects.exclude(management_ip=None)
    for idx, asset in enumerate(assets):
        try:
            ip = IPAddress.objects.get(
                address=asset.management_ip,
            )
        except IPAddress.DoesNotExist:
            ip = IPAddress(
                address=asset.management_ip,
            )
            ip.number = int(ipaddress.ip_address(ip.address))
        ip.hostname = asset.management_hostname
        ip.is_management = True
        ip.save()


def move_from_networks(apps, schema_editor):
    DataCenterAsset = apps.get_model('data_center', 'DataCenterAsset')
    IPAddress = apps.get_model('networks', 'IPAddress')
    ips = IPAddress.objects.exclude(is_management=False, base_object=None)
    for ip in ips:
        ip.base_object.management_ip = ip.address
        ip.base_object.management_hostname = ip.hostname
        ip.base_object.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0009_auto_20160310_0957'),
        ('networks', '0002_auto_20160310_1425'),
    ]

    operations = [
        migrations.RunPython(
            move_to_networks, reverse_code=move_from_networks
        ),
        migrations.RemoveField(
            model_name='datacenterasset',
            name='management_hostname',
        ),
        migrations.RemoveField(
            model_name='datacenterasset',
            name='management_ip',
        ),
    ]
