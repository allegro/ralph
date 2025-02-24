# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models
import ralph.trade_marks.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0033_auto_20211115_1125"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("domains", "0007_auto_20200909_1012"),
        ("trade_marks", "0014_auto_20211207_1118"),
    ]

    operations = [
        migrations.CreateModel(
            name="UtilityModel",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                        parent_link=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("number", models.CharField(max_length=255)),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=ralph.trade_marks.models.upload_dir,
                    ),
                ),
                ("classes", models.CharField(max_length=255)),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_to", models.DateField(blank=True, null=True)),
                (
                    "order_number_url",
                    models.URLField(max_length=255, blank=True, null=True),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        default=5,
                        choices=[
                            (1, "Application filed"),
                            (2, "Application refused"),
                            (3, "Application withdrawn"),
                            (4, "Application opposed"),
                            (5, "Registered"),
                            (6, "Registration invalidated"),
                            (7, "Registration expired"),
                        ],
                    ),
                ),
                (
                    "database_link",
                    models.URLField(max_length=255, blank=True, null=True),
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
                        related_name="utilitymodel_business_owner",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "holder",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        to="assets.AssetHolder",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "registrar_institution",
                    models.ForeignKey(
                        null=True,
                        to="trade_marks.TradeMarkRegistrarInstitution",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "technical_owner",
                    models.ForeignKey(
                        related_name="utilitymodel_technical_owner",
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
            name="UtilityModelAdditionalCountry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(
                        to="trade_marks.TradeMarkCountry",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "utility_model",
                    models.ForeignKey(
                        to="trade_marks.UtilityModel",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Utility Model Additional Country",
                "verbose_name_plural": "Utility Model Additional Countries",
            },
        ),
        migrations.CreateModel(
            name="UtilityModelLinkedDomains",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        related_name="utility_model",
                        to="domains.Domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "utility_model",
                    models.ForeignKey(
                        to="trade_marks.UtilityModel",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Utility Model Linked Domain",
                "verbose_name_plural": "Utility Model Linked Domains",
            },
        ),
        migrations.AlterUniqueTogether(
            name="utilitymodellinkeddomains",
            unique_together=set([("utility_model", "domain")]),
        ),
        migrations.AlterUniqueTogether(
            name="utilitymodeladditionalcountry",
            unique_together=set([("country", "utility_model")]),
        ),
    ]
