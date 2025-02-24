# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taggit", "0002_auto_20150616_2121"),
        ("assets", "0008_auto_20160122_1429"),
    ]

    operations = [
        migrations.CreateModel(
            name="SecurityScan",
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
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(verbose_name="last modified", auto_now=True),
                ),
                ("last_scan_date", models.DateTimeField()),
                (
                    "scan_status",
                    models.PositiveIntegerField(
                        choices=[(1, "ok"), (2, "fail"), (3, "error")]
                    ),
                ),
                ("next_scan_date", models.DateTimeField()),
                ("details_url", models.URLField(max_length=255, blank=True)),
                ("rescan_url", models.URLField(verbose_name="Rescan url", blank=True)),
                (
                    "base_object",
                    models.ForeignKey(
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        help_text="A comma-separated list of tags.",
                        verbose_name="Tags",
                        to="taggit.Tag",
                        through="taggit.TaggedItem",
                        blank=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Vulnerability",
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
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(verbose_name="last modified", auto_now=True),
                ),
                ("name", models.CharField(verbose_name="name", max_length=1024)),
                ("patch_deadline", models.DateTimeField(null=True, blank=True)),
                (
                    "risk",
                    models.PositiveIntegerField(
                        null=True,
                        choices=[(1, "low"), (2, "medium"), (3, "high")],
                        blank=True,
                    ),
                ),
                (
                    "external_vulnerability_id",
                    models.IntegerField(
                        help_text="Id of vulnerability from external system",
                        unique=True,
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        help_text="A comma-separated list of tags.",
                        verbose_name="Tags",
                        to="taggit.Tag",
                        through="taggit.TaggedItem",
                        blank=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="securityscan",
            name="vulnerabilities",
            field=models.ManyToManyField(to="security.Vulnerability"),
        ),
    ]
