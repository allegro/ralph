# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0009_auto_20170522_0745"),
    ]

    operations = [
        migrations.AddField(
            model_name="cloudprovider",
            name="cloud_sync_driver",
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="cloudprovider",
            name="cloud_sync_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
