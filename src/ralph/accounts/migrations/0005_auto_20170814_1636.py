# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_region_stocktaking_enabled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ralphuser",
            name="gender",
            field=models.PositiveIntegerField(
                choices=[(1, "female"), (2, "male"), (3, "unspecified")],
                verbose_name="gender",
                default=3,
            ),
        ),
    ]
