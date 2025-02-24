# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Domain",
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
                    "name",
                    models.CharField(
                        verbose_name="Domain name",
                        help_text="Full domain name",
                        unique=True,
                        max_length=255,
                    ),
                ),
                (
                    "domain_status",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "Active"),
                            (2, "Pending lapse"),
                            (3, "Pending transfer away"),
                            (4, "Lapsed (inactive)"),
                            (5, "Transfered away"),
                        ],
                        default=1,
                    ),
                ),
                (
                    "business_owner",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        blank=True,
                        null=True,
                        help_text="Business contact person for a domain",
                        related_name="domaincontract_business_owner",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "business_segment",
                    models.ForeignKey(
                        to="assets.BusinessSegment",
                        blank=True,
                        null=True,
                        help_text="Business segment for a domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "domain_holder",
                    models.ForeignKey(
                        to="assets.AssetHolder",
                        blank=True,
                        null=True,
                        help_text="Company which receives invoice for the domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "technical_owner",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        blank=True,
                        null=True,
                        help_text="Technical contact person for a domain",
                        related_name="domaincontract_technical_owner",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("assets.baseobject", ralph.lib.mixins.models.AdminAbsoluteUrlMixin),
        ),
        migrations.CreateModel(
            name="DomainContract",
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
                ("expiration_date", models.DateField(blank=True, null=True)),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        verbose_name="Price",
                        blank=True,
                        null=True,
                        help_text="Price for domain renewal for given period",
                        max_digits=15,
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        to="domains.Domain", on_delete=django.db.models.deletion.CASCADE
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="DomainRegistrant",
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
            model_name="domaincontract",
            name="registrant",
            field=models.ForeignKey(
                to="domains.DomainRegistrant",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
