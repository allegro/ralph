# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0016_fibrechannelcard"),
    ]

    operations = [
        migrations.CreateModel(
            name="Processor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(verbose_name="last modified", auto_now=True),
                ),
                (
                    "model_name",
                    models.CharField(
                        null=True, verbose_name="model name", blank=True, max_length=255
                    ),
                ),
                (
                    "speed",
                    models.PositiveIntegerField(
                        null=True, verbose_name="speed (MHz)", blank=True
                    ),
                ),
                ("cores", models.PositiveIntegerField(null=True, blank=True)),
                (
                    "base_object",
                    models.ForeignKey(
                        related_name="processor_set",
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        blank=True,
                        null=True,
                        verbose_name="model",
                        to="assets.ComponentModel",
                        default=None,
                    ),
                ),
            ],
            options={
                "verbose_name": "processor",
                "verbose_name_plural": "processors",
            },
        ),
    ]
