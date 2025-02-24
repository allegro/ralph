# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import django_extensions.db.fields.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dashboard",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="date created"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(verbose_name="last modified", auto_now=True),
                ),
                ("active", models.BooleanField(default=True)),
                (
                    "description",
                    models.CharField(
                        max_length=250, verbose_name="description", blank=True
                    ),
                ),
                ("interval", models.PositiveSmallIntegerField(default=60)),
            ],
            options={
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Graph",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="date created"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(verbose_name="last modified", auto_now=True),
                ),
                (
                    "description",
                    models.CharField(
                        max_length=250, verbose_name="description", blank=True
                    ),
                ),
                (
                    "aggregate_type",
                    models.PositiveIntegerField(
                        choices=[(1, "Count"), (2, "Max"), (3, "Sum")]
                    ),
                ),
                (
                    "chart_type",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "Verical Bar"),
                            (2, "Horizontal Bar"),
                            (3, "Pie Chart"),
                        ]
                    ),
                ),
                ("params", django_extensions.db.fields.json.JSONField(blank=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "model",
                    models.ForeignKey(
                        to="contenttypes.ContentType",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="dashboard",
            name="graphs",
            field=models.ManyToManyField(to="dashboards.Graph", blank=True),
        ),
    ]
