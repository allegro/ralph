# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import mptt.fields
import taggit.managers
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0004_auto_20151204_0758"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        migrations.CreateModel(
            name="Operation",
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
                ("title", models.CharField(max_length=350, verbose_name="title")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description", null=True),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        verbose_name="status",
                        choices=[
                            (1, "open"),
                            (2, "in progress"),
                            (3, "resolved"),
                            (4, "closed"),
                        ],
                    ),
                ),
                (
                    "ticket_id",
                    ralph.lib.mixins.fields.NullableCharField(
                        help_text="External system ticket identifier",
                        blank=True,
                        max_length=20,
                        verbose_name="ticket id",
                        null=True,
                    ),
                ),
                (
                    "created_date",
                    models.DateTimeField(
                        blank=True, verbose_name="created date", null=True
                    ),
                ),
                (
                    "update_date",
                    models.DateTimeField(
                        blank=True, verbose_name="updated date", null=True
                    ),
                ),
                (
                    "resolved_date",
                    models.DateTimeField(
                        blank=True, verbose_name="resolved date", null=True
                    ),
                ),
                (
                    "asignee",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="asignee",
                        null=True,
                        related_name="operations",
                        blank=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "base_objects",
                    models.ManyToManyField(
                        blank=True,
                        to="assets.BaseObject",
                        verbose_name="objects",
                        related_name="operations",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        to="taggit.Tag",
                        help_text="A comma-separated list of tags.",
                        verbose_name="Tags",
                        through="taggit.TaggedItem",
                        blank=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="OperationType",
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
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
                ("lft", models.PositiveIntegerField(editable=False, db_index=True)),
                ("rght", models.PositiveIntegerField(editable=False, db_index=True)),
                ("tree_id", models.PositiveIntegerField(editable=False, db_index=True)),
                ("level", models.PositiveIntegerField(editable=False, db_index=True)),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        to="operations.OperationType",
                        null=True,
                        related_name="children",
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="operation",
            name="type",
            field=mptt.fields.TreeForeignKey(
                to="operations.OperationType",
                verbose_name="type",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.CreateModel(
            name="Change",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("operations.operation",),
        ),
        migrations.CreateModel(
            name="Failure",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("operations.operation",),
        ),
        migrations.CreateModel(
            name="Incident",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("operations.operation",),
        ),
        migrations.CreateModel(
            name="Problem",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("operations.operation",),
        ),
    ]
