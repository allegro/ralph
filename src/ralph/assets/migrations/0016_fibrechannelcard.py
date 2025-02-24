# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0015_auto_20160701_0952"),
    ]

    operations = [
        migrations.CreateModel(
            name="FibreChannelCard",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
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
                    "firmware_version",
                    models.CharField(
                        null=True,
                        verbose_name="firmware version",
                        blank=True,
                        max_length=255,
                    ),
                ),
                (
                    "speed",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "1 Gbit"),
                            (2, "2 Gbit"),
                            (3, "4 Gbit"),
                            (4, "8 Gbit"),
                            (5, "16 Gbit"),
                            (6, "32 Gbit"),
                            (11, "unknown speed"),
                        ],
                        verbose_name="speed",
                        default=11,
                    ),
                ),
                (
                    "wwn",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="WWN",
                        blank=True,
                        default=None,
                        max_length=255,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        to="assets.BaseObject",
                        related_name="fibrechannelcard_set",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="model",
                        blank=True,
                        default=None,
                        to="assets.ComponentModel",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "fibre channel card",
                "verbose_name_plural": "fibre channel cards",
            },
        ),
    ]
