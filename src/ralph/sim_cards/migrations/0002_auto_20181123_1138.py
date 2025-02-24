# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("sim_cards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SIMCardFeatures",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
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
            model_name="simcard",
            name="features",
            field=models.ManyToManyField(blank=True, to="sim_cards.SIMCardFeatures"),
        ),
    ]
