# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Support",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
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
                ("contract_id", models.CharField(max_length=50)),
                ("description", models.CharField(blank=True, max_length=100)),
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
                ("date_from", models.DateField(blank=True, null=True)),
                ("date_to", models.DateField()),
                ("escalation_path", models.CharField(blank=True, max_length=200)),
                ("contract_terms", models.TextField(blank=True)),
                ("sla_type", models.CharField(blank=True, max_length=200)),
                (
                    "status",
                    models.PositiveSmallIntegerField(
                        verbose_name="status", choices=[(1, "new")], default=1
                    ),
                ),
                ("producer", models.CharField(blank=True, max_length=100)),
                ("supplier", models.CharField(blank=True, max_length=100)),
                ("serial_no", models.CharField(blank=True, max_length=100)),
                (
                    "invoice_no",
                    models.CharField(blank=True, db_index=True, max_length=100),
                ),
                (
                    "invoice_date",
                    models.DateField(
                        verbose_name="Invoice date", blank=True, null=True
                    ),
                ),
                ("period_in_months", models.IntegerField(blank=True, null=True)),
                (
                    "base_objects",
                    models.ManyToManyField(
                        to="assets.BaseObject", related_name="supports"
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
                (
                    "property_of",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="assets.AssetHolder",
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        to="accounts.Region",
                        on_delete=django.db.models.deletion.CASCADE,
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
            name="SupportType",
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
        migrations.AddField(
            model_name="support",
            name="support_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                default=None,
                to="supports.SupportType",
                blank=True,
                null=True,
            ),
        ),
    ]
