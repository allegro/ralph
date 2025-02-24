# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0005_auto_20170323_1425"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operation",
            name="status",
            field=models.PositiveIntegerField(
                verbose_name="status",
                choices=[
                    (1, "open"),
                    (2, "in progress"),
                    (3, "resolved"),
                    (4, "closed"),
                    (5, "reopened"),
                    (6, "todo"),
                    (7, "blocked"),
                ],
                default=1,
            ),
        ),
    ]
