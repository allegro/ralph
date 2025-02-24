# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ralph.data_center.models.physical import ACCESSORY_DATA


def initial_accessory(apps, schema_editor):
    Accessory = apps.get_model("data_center", "Accessory")
    for name in ACCESSORY_DATA:
        Accessory.objects.get_or_create(name=name)


def unload_initial_accessory(apps, schema_editor):
    Accessory = apps.get_model("data_center", "Accessory")
    Accessory.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0004_auto_20151204_0758"),
    ]

    operations = [
        migrations.RunPython(initial_accessory, reverse_code=unload_initial_accessory),
    ]
