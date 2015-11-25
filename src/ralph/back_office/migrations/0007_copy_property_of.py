# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def copy_property_of(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    BackOfficeAsset = apps.get_model("back_office", "BackOfficeAsset")

    for bo in BackOfficeAsset.objects.all():
        Asset.objects.filter(pk=bo.pk).update(property_of_2=bo.property_of)


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0006_auto_20151110_0949'),
        ('assets', '0008_asset_property_of'),
    ]

    operations = [
        migrations.RunPython(copy_property_of),
        migrations.RemoveField(
            model_name='backofficeasset',
            name='property_of',
        ),
    ]
