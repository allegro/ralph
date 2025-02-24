# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def move_from_base_object_to_ethernet(apps, schema_editor):
    IPAddress = apps.get_model("networks", "IPAddress")
    Ethernet = apps.get_model("assets", "Ethernet")

    for ip in IPAddress.objects.filter(base_object__isnull=False):
        if not ip.ethernet:
            ip.ethernet = Ethernet.objects.create(base_object=ip.base_object)
        else:
            ip.ethernet.base_object_id = ip.base_object_id
        ip.ethernet.save()
        ip.save()


def move_from_ethernet_to_base_object(apps, schema_editor):
    Ethernet = apps.get_model("assets", "Ethernet")
    for eth in Ethernet.objects.filter(
        ipaddress__isnull=False,
    ):
        eth.ipaddress.base_object_id = eth.base_object_id
        eth.ipaddress.save()


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0002_add_ethernet_field"),
        ("data_center", "0014_custom_move_managment_to_networks"),
    ]

    operations = [
        migrations.RunPython(
            move_from_base_object_to_ethernet,
            reverse_code=move_from_ethernet_to_base_object,
        )
    ]
