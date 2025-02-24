# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0015_auto_20160615_2140"),
    ]

    operations = [
        migrations.AddField(
            model_name="diskshare",
            name="model_name",
            field=models.CharField(
                max_length=255, verbose_name="model name", blank=True, null=True
            ),
        ),
    ]
