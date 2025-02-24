# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
        ("back_office", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseObjectLicence",
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
                ("quantity", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name="Licence",
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
                    "number_bought",
                    models.IntegerField(verbose_name="Number of purchased items"),
                ),
                (
                    "sn",
                    models.TextField(verbose_name="SN / Key", blank=True, null=True),
                ),
                (
                    "niw",
                    models.CharField(
                        verbose_name="Inventory number",
                        default="N/A",
                        unique=True,
                        max_length=200,
                    ),
                ),
                (
                    "invoice_date",
                    models.DateField(
                        verbose_name="Invoice date", blank=True, null=True
                    ),
                ),
                (
                    "valid_thru",
                    models.DateField(
                        blank=True,
                        null=True,
                        help_text="Leave blank if this licence is perpetual",
                    ),
                ),
                ("order_no", models.CharField(blank=True, null=True, max_length=50)),
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
                (
                    "accounting_id",
                    models.CharField(
                        blank=True,
                        null=True,
                        help_text="Any value to help your accounting department identify this licence",
                        max_length=200,
                    ),
                ),
                ("provider", models.CharField(blank=True, null=True, max_length=100)),
                (
                    "invoice_no",
                    models.CharField(
                        blank=True, db_index=True, null=True, max_length=128
                    ),
                ),
                (
                    "license_details",
                    models.CharField(
                        verbose_name="License details",
                        blank=True,
                        default="",
                        max_length=1024,
                    ),
                ),
                (
                    "base_objects",
                    models.ManyToManyField(
                        verbose_name="Assigned base objects",
                        through="licences.BaseObjectLicence",
                        to="assets.BaseObject",
                        related_name="_licence_base_objects_+",
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
            bases=(
                ralph.lib.mixins.models.AdminAbsoluteUrlMixin,
                "assets.baseobject",
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="LicenceType",
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
            name="LicenceUser",
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
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "licence",
                    models.ForeignKey(
                        to="licences.Licence",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        related_name="licences",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Software",
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
                    "asset_type",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "back office"),
                            (2, "data center"),
                            (3, "part"),
                            (4, "all"),
                        ],
                        default=4,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "software categories",
            },
        ),
        migrations.AddField(
            model_name="licence",
            name="licence_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                help_text="Should be like 'per processor' or 'per machine' and so on. ",
                to="licences.LicenceType",
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="manufacturer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.Manufacturer",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="office_infrastructure",
            field=models.ForeignKey(
                to="back_office.OfficeInfrastructure",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="property_of",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.AssetHolder",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="region",
            field=models.ForeignKey(
                to="accounts.Region", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="software",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="licences.Software"
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="users",
            field=models.ManyToManyField(
                through="licences.LicenceUser",
                to=settings.AUTH_USER_MODEL,
                related_name="_licence_users_+",
            ),
        ),
        migrations.AddField(
            model_name="baseobjectlicence",
            name="base_object",
            field=models.ForeignKey(
                verbose_name="Asset",
                to="assets.BaseObject",
                related_name="licences",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="baseobjectlicence",
            name="licence",
            field=models.ForeignKey(
                to="licences.Licence", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AlterUniqueTogether(
            name="licenceuser",
            unique_together=set([("licence", "user")]),
        ),
        migrations.AlterUniqueTogether(
            name="baseobjectlicence",
            unique_together=set([("licence", "base_object")]),
        ),
    ]
