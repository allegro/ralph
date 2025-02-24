# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0002_auto_20151125_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="force_depreciation",
            field=models.BooleanField(
                default=False,
                help_text="Check if you no longer want to bill for this asset",
            ),
        ),
    ]
