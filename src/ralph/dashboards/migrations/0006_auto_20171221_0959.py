# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboards", "0005_auto_20170927_1505"),
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
                    (5, "Sum with zeros"),
                    (6, "Sum boolean values"),
                    (7, "Sum negated boolean values"),
                    (8, "Ratio"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="graph",
            name="chart_type",
            field=models.PositiveIntegerField(
                choices=[(1, "Vertical Bar"), (2, "Horizontal Bar"), (3, "Pie Chart")]
            ),
        ),
    ]
