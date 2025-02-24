# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0028_auto_20230831_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datacenter",
            name="type",
            field=models.PositiveIntegerField(
                verbose_name="data center type",
                blank=True,
                null=True,
                choices=[
                    (1, "dc"),
                    (2, "cowork"),
                    (3, "callcenter"),
                    (4, "depot"),
                    (5, "warehouse"),
                    (6, "retail"),
                    (7, "office"),
                ],
            ),
        ),
    ]
