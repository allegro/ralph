# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0025_auto_20170331_1341"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManufacturerKind",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", max_length=255, unique=True),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.AddField(
            model_name="manufacturer",
            name="manufacturer_kind",
            field=models.ForeignKey(
                verbose_name="manufacturer kind",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="assets.ManufacturerKind",
                blank=True,
            ),
        ),
    ]
