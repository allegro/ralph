# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Car2",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "manufacturer",
                    models.ForeignKey(
                        to="tests.Manufacturer",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="baseobjectforeignkeymodel",
            name="base_object",
            field=ralph.lib.mixins.fields.BaseObjectForeignKey(
                to="assets.BaseObject", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
    ]
