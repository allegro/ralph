# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("domains", "0006_auto_20180725_1216"),
        ("assets", "0027_asset_buyout_date"),
        ("accounts", "0006_remove_ralphuser_gender"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderAdditionalMarking",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(unique=True, verbose_name="name", max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="last modified"),
                ),
            ],
            options={
                "abstract": False,
                "ordering": ["name"],
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="TradeMark",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        parent_link=True,
                        auto_created=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="Trade Mark name", max_length=255),
                ),
                (
                    "registrant_number",
                    models.CharField(verbose_name="Registrant number", max_length=255),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark type",
                        choices=[
                            (1, "Word"),
                            (2, "Figurative"),
                            (3, "Word - Figurative"),
                        ],
                        default=2,
                    ),
                ),
                (
                    "registrant_class",
                    models.CharField(verbose_name="Registrant class", max_length=255),
                ),
                ("valid_to", models.DateField()),
                (
                    "order_number_url",
                    models.URLField(null=True, blank=True, max_length=255),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark status",
                        choices=[
                            (1, "Application filed"),
                            (2, "Application refused"),
                            (3, "Application withdrawn"),
                            (4, "Application opposed"),
                            (5, "Registered"),
                            (6, "Registration invalidated"),
                            (7, "Registration expired"),
                        ],
                        default=5,
                    ),
                ),
                (
                    "additional_markings",
                    models.ManyToManyField(
                        blank=True, to="trade_marks.ProviderAdditionalMarking"
                    ),
                ),
                (
                    "business_owner",
                    models.ForeignKey(
                        related_name="trademark_business_owner",
                        to=settings.AUTH_USER_MODEL,
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
            name="TradeMarksLinkedDomains",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        related_name="trade_mark",
                        to="domains.Domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "trade_mark",
                    models.ForeignKey(
                        to="trade_marks.TradeMark",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="trademark",
            name="domains",
            field=models.ManyToManyField(
                related_name="_trademark_domains_+",
                through="trade_marks.TradeMarksLinkedDomains",
                to="domains.Domain",
            ),
        ),
        migrations.AddField(
            model_name="trademark",
            name="holder",
            field=models.ForeignKey(
                to="assets.AssetHolder",
                verbose_name="Trade Mark holder",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="trademark",
            name="region",
            field=models.ForeignKey(
                to="accounts.Region", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="trademark",
            name="technical_owner",
            field=models.ForeignKey(
                related_name="trademark_technical_owner",
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="trademarkslinkeddomains",
            unique_together=set([("trade_mark", "domain")]),
        ),
    ]
