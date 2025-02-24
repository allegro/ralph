# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboards", "0004_auto_20170926_1547"),
    ]

    operations = [
        migrations.AlterField(
            model_name="graph",
            name="aggregate_type",
            field=models.PositiveIntegerField(
                choices=[
                    (1, "Count"),
                    (2, "Count with zeros"),
                    (3, "Max"),
                    (4, "Sum"),
                    (5, "Sum boolean values"),
                    (6, "Ratio"),
                ]
            ),
        ),
    ]
