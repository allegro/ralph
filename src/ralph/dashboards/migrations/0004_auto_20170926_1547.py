# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboards", "0003_graph_push_to_statsd"),
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
                    (5, "Ratio"),
                ]
            ),
        ),
    ]
