# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0005_warehouse_stocktaking_tag_suffix"),
    ]

    operations = [
        migrations.AlterField(
            model_name="warehouse",
            name="stocktaking_tag_suffix",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
    ]
