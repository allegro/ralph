# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0017_processor"),
    ]

    operations = [
        migrations.CreateModel(
            name="Disk",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
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
                        verbose_name="model name", blank=True, null=True, max_length=255
                    ),
                ),
                ("size", models.PositiveIntegerField(verbose_name="size (GiB)")),
                (
                    "serial_number",
                    models.CharField(
                        verbose_name="serial number",
                        blank=True,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "slot",
                    models.PositiveIntegerField(
                        verbose_name="slot number", blank=True, null=True
                    ),
                ),
                (
                    "firmware_version",
                    models.CharField(
                        verbose_name="firmware version",
                        blank=True,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        to="assets.BaseObject",
                        related_name="disk_set",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        verbose_name="model",
                        to="assets.ComponentModel",
                        null=True,
                        default=None,
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                    ),
                ),
            ],
            options={
                "verbose_name": "disk",
                "verbose_name_plural": "disks",
            },
        ),
    ]
