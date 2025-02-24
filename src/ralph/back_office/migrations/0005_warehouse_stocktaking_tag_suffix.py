# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0004_warehouse_stocktaking_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouse",
            name="stocktaking_tag_suffix",
            field=models.CharField(max_length=8, default=""),
        ),
    ]
