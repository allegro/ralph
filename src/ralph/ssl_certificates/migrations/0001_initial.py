# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0027_asset_buyout_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SSLCertificate",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        to="assets.BaseObject",
                        parent_link=True,
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        verbose_name="certificate name",
                        help_text="Full certificate name",
                        max_length=255,
                    ),
                ),
                (
                    "certificate_type",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "EV"),
                            (2, "OV"),
                            (3, "DV"),
                            (4, "Wildcard"),
                            (5, "Multisan"),
                            (6, "CA ENT"),
                        ],
                        default=2,
                    ),
                ),
                ("date_from", models.DateField(null=True, blank=True)),
                ("date_to", models.DateField()),
                (
                    "san",
                    models.TextField(
                        help_text="All Subject Alternative Names", blank=True
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        null=True,
                        blank=True,
                        max_digits=10,
                    ),
                ),
                (
                    "business_owner",
                    models.ForeignKey(
                        related_name="certificates_business_owner",
                        to=settings.AUTH_USER_MODEL,
                        help_text="Business contact person for a certificate",
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "issued_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="assets.Manufacturer",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "technical_owner",
                    models.ForeignKey(
                        related_name="certificates_technical_owner",
                        to=settings.AUTH_USER_MODEL,
                        help_text="Technical contact person for a certificate",
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, "assets.baseobject"),
        ),
    ]
