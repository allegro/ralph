# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboards", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="graph",
            name="aggregate_type",
            field=models.PositiveIntegerField(
                choices=[(1, "Count"), (2, "Max"), (3, "Sum"), (4, "Ratio")]
            ),
        ),
    ]
