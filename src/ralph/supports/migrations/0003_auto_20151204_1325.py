# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0002_auto_20151204_0758"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseObjectsSupport",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
            ],
            options={
                "db_table": "supports_support_base_objects",
                "managed": False,
            },
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="support",
                    name="base_objects",
                    field=models.ManyToManyField(
                        related_name="supports",
                        to="assets.BaseObject",
                        through="supports.BaseObjectsSupport",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
