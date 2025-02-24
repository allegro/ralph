# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0013_auto_20160615_2140"),
    ]

    operations = [
        migrations.CreateModel(
            name="Memory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="date created"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="last modified"),
                ),
                ("label", models.CharField(max_length=255, verbose_name="name")),
                ("size", models.PositiveIntegerField(verbose_name="size (MiB)")),
                (
                    "speed",
                    models.PositiveIntegerField(
                        null=True, blank=True, verbose_name="speed (MHz)"
                    ),
                ),
                (
                    "slot_no",
                    models.PositiveIntegerField(
                        null=True, blank=True, verbose_name="slot number"
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        related_name="memory_set",
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="assets.ComponentModel",
                        blank=True,
                        default=None,
                        null=True,
                        verbose_name="model",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "memories",
                "verbose_name": "memory",
            },
        ),
    ]
