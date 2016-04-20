# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def move_from_base_object_to_ethernet(apps, schema_editor):
    IPAddress = apps.get_model('networks', 'IPAddress')
    Ethernet = apps.get_model('assets', 'Ethernet')

    for ip in IPAddress.objects.filter(
        base_object__isnull=False
    ):
        if not ip.ethernet:
            ip.ethernet = Ethernet.objects.create(base_object=ip.base_object)
        else:
            ip.ethernet.base_object = ip.base_object
        ip.ethernet.save()
        ip.save()


def move_from_ethernet_to_base_object(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0007_network_dns_servers'),
    ]

    operations = [
        migrations.RunPython(
            move_from_base_object_to_ethernet,
            reverse_code=move_from_ethernet_to_base_object
        )
    ]
