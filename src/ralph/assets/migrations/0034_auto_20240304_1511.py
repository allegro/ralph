# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0033_auto_20211115_1125"),
    ]

    operations = [
        migrations.AddField(
            model_name="processor",
            name="logical_cores",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="processor",
            name="cores",
            field=models.PositiveIntegerField(
                verbose_name="physical cores", blank=True, null=True
            ),
        ),
    ]
