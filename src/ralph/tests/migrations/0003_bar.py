# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0002_auto_20160119_0914"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bar",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("date", models.DateField()),
                ("price", models.DecimalField(max_digits=5, decimal_places=2)),
                ("count", models.IntegerField(default=0)),
            ],
        ),
    ]
