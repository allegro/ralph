# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import re

import django.core.validators
import django.db.models.deletion
import mptt.fields
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_region_country"),
        ("assets", "0011_auto_20160603_0742"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfigurationClass",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
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
                    "class_name",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(regex="\\w+")
                        ],
                        verbose_name="class name",
                        help_text="ex. puppet class",
                        max_length=255,
                    ),
                ),
                (
                    "path",
                    models.TextField(
                        editable=False,
                        verbose_name="path",
                        default="",
                        help_text="path is constructed from name of module and name of class",
                        blank=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "configuration class",
                "ordering": ("path",),
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ConfigurationModule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
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
                    "name",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(regex="\\w+")
                        ],
                        verbose_name="name",
                        help_text="module name (ex. directory name in puppet)",
                        max_length=255,
                    ),
                ),
                ("lft", models.PositiveIntegerField(editable=False, db_index=True)),
                ("rght", models.PositiveIntegerField(editable=False, db_index=True)),
                ("tree_id", models.PositiveIntegerField(editable=False, db_index=True)),
                ("level", models.PositiveIntegerField(editable=False, db_index=True)),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        related_name="children_modules",
                        verbose_name="parent module",
                        to="assets.ConfigurationModule",
                        default=None,
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "support_team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="team",
                        to="accounts.Team",
                        default=None,
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "configuration module",
                "ordering": ("parent__name", "name"),
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Ethernet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
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
                    "label",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="name", max_length=255, blank=True, null=True
                    ),
                ),
                (
                    "mac",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="MAC address",
                        validators=[
                            django.core.validators.RegexValidator(
                                message="'%(value)s' is not a valid MAC address.",
                                regex=re.compile(
                                    "^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$",
                                    32,
                                ),
                            )
                        ],
                        unique=True,
                        max_length=24,
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "speed",
                    models.PositiveIntegerField(
                        verbose_name="speed",
                        default=11,
                        choices=[
                            (1, "10 Mbps"),
                            (2, "100 Mbps"),
                            (3, "1 Gbps"),
                            (4, "10 Gbps"),
                            (5, "40 Gbps"),
                            (6, "100 Gbps"),
                            (11, "unknown speed"),
                        ],
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        related_name="ethernet",
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="model",
                        to="assets.ComponentModel",
                        default=None,
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "ethernet",
                "verbose_name_plural": "ethernets",
                "ordering": ("base_object", "mac"),
            },
        ),
        migrations.AddField(
            model_name="genericcomponent",
            name="created",
            field=models.DateTimeField(
                verbose_name="date created",
                default=datetime.datetime(2016, 6, 6, 14, 7, 47, 639689),
                auto_now_add=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="genericcomponent",
            name="modified",
            field=models.DateTimeField(
                verbose_name="last modified",
                default=datetime.datetime(2016, 6, 6, 14, 7, 51, 223597),
                auto_now=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="assetlasthostname",
            name="postfix",
            field=models.CharField(db_index=True, max_length=30),
        ),
        migrations.AlterField(
            model_name="assetlasthostname",
            name="prefix",
            field=models.CharField(db_index=True, max_length=30),
        ),
        migrations.AddField(
            model_name="configurationclass",
            name="module",
            field=models.ForeignKey(
                related_name="configuration_classes",
                to="assets.ConfigurationModule",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobject",
            name="configuration_path",
            field=models.ForeignKey(
                to="assets.ConfigurationClass",
                verbose_name="configuration path",
                help_text="path to configuration for this object, for example path to puppet class",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="configurationmodule",
            unique_together=set([("parent", "name")]),
        ),
        migrations.AlterUniqueTogether(
            name="configurationclass",
            unique_together=set([("module", "class_name")]),
        ),
    ]
