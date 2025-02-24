# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ipaddress

import django
from django.db import migrations


def move_to_networks(apps, schema_editor):
    DataCenterAsset = apps.get_model("data_center", "DataCenterAsset")
    IPAddress = apps.get_model("networks", "IPAddress")
    assets = DataCenterAsset.objects.exclude(management_ip_old=None)
    for idx, asset in enumerate(assets):
        try:
            ip = IPAddress.objects.get(
                address=asset.management_ip_old,
            )
        except IPAddress.DoesNotExist:
            ip = IPAddress(
                address=asset.management_ip_old,
            )
            ip.number = int(ipaddress.ip_address(ip.address))
        ip.hostname = asset.management_hostname_old
        ip.is_management = True
        ip.base_object = asset
        ip.save()


def move_from_networks(apps, schema_editor):
    IPAddress = apps.get_model("networks", "IPAddress")
    ips = IPAddress.objects.filter(
        is_management=True, base_object__asset__datacenterasset__isnull=False
    )
    for ip in ips:
        dca = ip.base_object.asset.datacenterasset
        dca.management_ip_old = ip.address
        dca.management_hostname_old = ip.hostname
        dca.save()


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0013_auto_20160606_1438"),
        ("networks", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="datacenterasset",
            managers=[
                ("objects", django.db.models.manager.Manager()),
            ],
        ),
        # rename first to `management_ip_old` because there is now property
        # `management_ip` in DataCenterAsset which "hides" database field
        # thus should not be used directly
        migrations.RenameField(
            model_name="datacenterasset",
            old_name="management_ip",
            new_name="management_ip_old",
        ),
        migrations.RenameField(
            model_name="datacenterasset",
            old_name="management_hostname",
            new_name="management_hostname_old",
        ),
        migrations.RunPython(move_to_networks, reverse_code=move_from_networks),
        migrations.RemoveField(
            model_name="datacenterasset",
            name="management_hostname_old",
        ),
        migrations.RemoveField(
            model_name="datacenterasset",
            name="management_ip_old",
        ),
    ]
