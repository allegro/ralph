# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0007_auto_20160122_1022"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetmodel",
            name="cores_count",
            field=models.PositiveIntegerField(verbose_name="Cores count", default=0),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="height_of_device",
            field=models.FloatField(
                verbose_name="Height of device",
                validators=[django.core.validators.MinValueValidator(0)],
                default=0,
            ),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="power_consumption",
            field=models.PositiveIntegerField(
                verbose_name="Power consumption", default=0
            ),
        ),
    ]
