# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackOfficeAsset",
            fields=[
                (
                    "asset_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.Asset",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("location", models.CharField(blank=True, null=True, max_length=128)),
                (
                    "purchase_order",
                    models.CharField(blank=True, null=True, max_length=50),
                ),
                (
                    "loan_end_date",
                    models.DateField(
                        verbose_name="Loan end date",
                        blank=True,
                        default=None,
                        null=True,
                    ),
                ),
                (
                    "status",
                    ralph.lib.transitions.fields.TransitionField(
                        choices=[
                            (1, "new"),
                            (2, "in progress"),
                            (3, "waiting for release"),
                            (4, "in use"),
                            (5, "loan"),
                            (6, "damaged"),
                            (7, "liquidated"),
                            (8, "in service"),
                            (9, "installed"),
                            (10, "free"),
                            (11, "reserved"),
                        ],
                        default=1,
                    ),
                ),
                (
                    "imei",
                    ralph.lib.mixins.fields.NullableCharField(
                        blank=True, null=True, unique=True, max_length=18
                    ),
                ),
            ],
            options={
                "verbose_name": "Back Office Asset",
                "verbose_name_plural": "Back Office Assets",
            },
            bases=("assets.asset", models.Model),
        ),
        migrations.CreateModel(
            name="OfficeInfrastructure",
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
                "verbose_name": "Office Infrastructure",
                "verbose_name_plural": "Office Infrastructures",
            },
        ),
        migrations.CreateModel(
            name="Warehouse",
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
        migrations.AddField(
            model_name="backofficeasset",
            name="office_infrastructure",
            field=models.ForeignKey(
                to="back_office.OfficeInfrastructure",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="backofficeasset",
            name="owner",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                null=True,
                related_name="assets_as_owner",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="backofficeasset",
            name="region",
            field=models.ForeignKey(
                to="accounts.Region", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="backofficeasset",
            name="user",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                null=True,
                related_name="assets_as_user",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="backofficeasset",
            name="warehouse",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="back_office.Warehouse"
            ),
        ),
    ]
