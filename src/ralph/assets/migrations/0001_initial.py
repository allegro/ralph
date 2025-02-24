# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
import django.db.models.deletion
import mptt.fields
import taggit.managers
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetHolder",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AssetLastHostname",
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
                ("prefix", models.CharField(db_index=True, max_length=8)),
                ("counter", models.PositiveIntegerField(default=1)),
                ("postfix", models.CharField(db_index=True, max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name="AssetModel",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        verbose_name="type",
                        choices=[
                            (1, "back office"),
                            (2, "data center"),
                            (3, "part"),
                            (4, "all"),
                        ],
                    ),
                ),
                (
                    "power_consumption",
                    models.PositiveIntegerField(
                        verbose_name="Power consumption", blank=True, default=0
                    ),
                ),
                (
                    "height_of_device",
                    models.FloatField(
                        verbose_name="Height of device",
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        blank=True,
                    ),
                ),
                (
                    "cores_count",
                    models.PositiveIntegerField(
                        verbose_name="Cores count", blank=True, default=0
                    ),
                ),
                (
                    "visualization_layout_front",
                    models.PositiveIntegerField(
                        verbose_name="visualization layout of front side",
                        choices=[
                            (1, "N/A"),
                            (2, "1x2"),
                            (3, "2x8"),
                            (4, "2x16 (A/B)"),
                            (5, "4x2"),
                        ],
                        blank=True,
                        default=1,
                    ),
                ),
                (
                    "visualization_layout_back",
                    models.PositiveIntegerField(
                        verbose_name="visualization layout of back side",
                        choices=[
                            (1, "N/A"),
                            (2, "1x2"),
                            (3, "2x8"),
                            (4, "2x16 (A/B)"),
                            (5, "4x2"),
                        ],
                        blank=True,
                        default=1,
                    ),
                ),
                ("has_parent", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "model",
                "verbose_name_plural": "models",
            },
        ),
        migrations.CreateModel(
            name="BaseObject",
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
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                ("remarks", models.TextField(blank=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="BudgetInfo",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Budget info",
                "verbose_name_plural": "Budgets info",
            },
        ),
        migrations.CreateModel(
            name="BusinessSegment",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                ("code", models.CharField(blank=True, default="", max_length=4)),
                ("imei_required", models.BooleanField(default=False)),
                ("lft", models.PositiveIntegerField(editable=False, db_index=True)),
                ("rght", models.PositiveIntegerField(editable=False, db_index=True)),
                ("tree_id", models.PositiveIntegerField(editable=False, db_index=True)),
                ("level", models.PositiveIntegerField(editable=False, db_index=True)),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        to="assets.Category",
                        blank=True,
                        null=True,
                        related_name="children",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
            },
        ),
        migrations.CreateModel(
            name="ComponentModel",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "speed",
                    models.PositiveIntegerField(
                        verbose_name="speed (MHz)", blank=True, default=0
                    ),
                ),
                (
                    "cores",
                    models.PositiveIntegerField(
                        verbose_name="number of cores", blank=True, default=0
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        verbose_name="size (MiB)", blank=True, default=0
                    ),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        verbose_name="component type",
                        choices=[
                            (1, "processor"),
                            (2, "memory"),
                            (3, "disk drive"),
                            (4, "ethernet card"),
                            (5, "expansion card"),
                            (6, "fibre channel card"),
                            (7, "disk share"),
                            (8, "unknown"),
                            (9, "management"),
                            (10, "power module"),
                            (11, "cooling device"),
                            (12, "media tray"),
                            (13, "chassis"),
                            (14, "backup"),
                            (15, "software"),
                            (16, "operating system"),
                        ],
                        default=8,
                    ),
                ),
                ("family", models.CharField(blank=True, default="", max_length=128)),
            ],
            options={
                "verbose_name": "component model",
                "verbose_name_plural": "component models",
            },
        ),
        migrations.CreateModel(
            name="Environment",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="GenericComponent",
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
                    "label",
                    models.CharField(
                        verbose_name="label",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "sn",
                    ralph.lib.mixins.fields.NullableCharField(
                        default=None,
                        unique=True,
                        max_length=255,
                        verbose_name="vendor SN",
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "generic component",
                "verbose_name_plural": "generic components",
            },
        ),
        migrations.CreateModel(
            name="Manufacturer",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProfitCenter",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "business_segment",
                    models.ForeignKey(
                        to="assets.BusinessSegment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Service",
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
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                (
                    "uid",
                    ralph.lib.mixins.fields.NullableCharField(
                        blank=True, null=True, unique=True, max_length=40
                    ),
                ),
                ("cost_center", models.CharField(blank=True, max_length=100)),
                (
                    "business_owners",
                    models.ManyToManyField(
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        related_name="services_business_owner",
                    ),
                ),
                (
                    "profit_center",
                    models.ForeignKey(
                        to="assets.ProfitCenter",
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "support_team",
                    models.ForeignKey(
                        to="accounts.Team",
                        blank=True,
                        null=True,
                        related_name="services",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "technical_owners",
                    models.ManyToManyField(
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        related_name="services_technical_owner",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Asset",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "hostname",
                    models.CharField(
                        verbose_name="hostname",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "sn",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="SN",
                        blank=True,
                        null=True,
                        unique=True,
                        max_length=200,
                    ),
                ),
                (
                    "barcode",
                    ralph.lib.mixins.fields.NullableCharField(
                        default=None,
                        unique=True,
                        max_length=200,
                        verbose_name="barcode",
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "niw",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="Inventory number",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=200,
                    ),
                ),
                ("required_support", models.BooleanField(default=False)),
                ("order_no", models.CharField(blank=True, null=True, max_length=50)),
                (
                    "invoice_no",
                    models.CharField(
                        blank=True, db_index=True, null=True, max_length=128
                    ),
                ),
                ("invoice_date", models.DateField(blank=True, null=True)),
                (
                    "price",
                    models.DecimalField(
                        blank=True,
                        default=0,
                        null=True,
                        decimal_places=2,
                        max_digits=10,
                    ),
                ),
                ("provider", models.CharField(blank=True, null=True, max_length=100)),
                (
                    "depreciation_rate",
                    models.DecimalField(
                        blank=True,
                        default=25,
                        help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .',
                        max_digits=5,
                        decimal_places=2,
                    ),
                ),
                (
                    "force_depreciation",
                    models.BooleanField(
                        help_text="Check if you no longer want to bill for this asset"
                    ),
                ),
                ("depreciation_end_date", models.DateField(blank=True, null=True)),
                (
                    "task_url",
                    models.URLField(
                        blank=True,
                        null=True,
                        help_text="External workflow system URL",
                        max_length=2048,
                    ),
                ),
                (
                    "budget_info",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        default=None,
                        to="assets.BudgetInfo",
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, "assets.baseobject"),
        ),
        migrations.CreateModel(
            name="ServiceEnvironment",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        to="assets.Environment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        to="assets.Service", on_delete=django.db.models.deletion.CASCADE
                    ),
                ),
            ],
            bases=("assets.baseobject",),
        ),
        migrations.AddField(
            model_name="genericcomponent",
            name="base_object",
            field=models.ForeignKey(
                to="assets.BaseObject",
                related_name="genericcomponent",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="genericcomponent",
            name="model",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                default=None,
                verbose_name="model",
                to="assets.ComponentModel",
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="componentmodel",
            unique_together=set([("speed", "cores", "size", "type", "family")]),
        ),
        migrations.AddField(
            model_name="baseobject",
            name="content_type",
            field=models.ForeignKey(
                to="contenttypes.ContentType",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobject",
            name="parent",
            field=models.ForeignKey(
                to="assets.BaseObject",
                blank=True,
                null=True,
                related_name="children",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobject",
            name="tags",
            field=taggit.managers.TaggableManager(
                through="taggit.TaggedItem",
                verbose_name="Tags",
                blank=True,
                to="taggit.Tag",
                help_text="A comma-separated list of tags.",
            ),
        ),
        migrations.AddField(
            model_name="assetmodel",
            name="category",
            field=mptt.fields.TreeForeignKey(
                to="assets.Category",
                null=True,
                related_name="models",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="assetmodel",
            name="manufacturer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.Manufacturer",
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="assetlasthostname",
            unique_together=set([("prefix", "postfix")]),
        ),
        migrations.AddField(
            model_name="service",
            name="environments",
            field=models.ManyToManyField(
                through="assets.ServiceEnvironment", to="assets.Environment"
            ),
        ),
        migrations.AddField(
            model_name="baseobject",
            name="service_env",
            field=models.ForeignKey(
                to="assets.ServiceEnvironment",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="model",
            field=models.ForeignKey(
                to="assets.AssetModel",
                related_name="assets",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="property_of",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.AssetHolder",
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="serviceenvironment",
            unique_together=set([("service", "environment")]),
        ),
    ]
