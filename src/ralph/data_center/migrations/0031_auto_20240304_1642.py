# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0030_auto_20240221_1004"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datacenterasset",
            name="leasing_rate",
            field=models.FloatField(verbose_name="Leasing rate", blank=True, null=True),
        ),
    ]
