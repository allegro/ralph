# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models
import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0009_auto_20181016_1252"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CellularCarrier",
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
                    "name",
                    models.CharField(verbose_name="name", max_length=255, unique=True),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="SIMCard",
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
                    "pin1",
                    models.CharField(
                        max_length=8,
                        blank=True,
                        null=True,
                        help_text="Required numeric characters only.",
                        validators=[
                            django.core.validators.MinLengthValidator(4),
                            django.core.validators.RegexValidator(
                                regex="^\\d+$",
                                message="Required numeric characters only.",
                            ),
                        ],
                    ),
                ),
                (
                    "puk1",
                    models.CharField(
                        max_length=16,
                        help_text="Required numeric characters only.",
                        validators=[
                            django.core.validators.MinLengthValidator(5),
                            django.core.validators.RegexValidator(
                                regex="^\\d+$",
                                message="Required numeric characters only.",
                            ),
                        ],
                    ),
                ),
                (
                    "pin2",
                    models.CharField(
                        max_length=8,
                        blank=True,
                        null=True,
                        help_text="Required numeric characters only.",
                        validators=[
                            django.core.validators.MinLengthValidator(4),
                            django.core.validators.RegexValidator(
                                regex="^\\d+$",
                                message="Required numeric characters only.",
                            ),
                        ],
                    ),
                ),
                (
                    "puk2",
                    models.CharField(
                        max_length=16,
                        blank=True,
                        null=True,
                        help_text="Required numeric characters only.",
                        validators=[
                            django.core.validators.MinLengthValidator(5),
                            django.core.validators.RegexValidator(
                                regex="^\\d+$",
                                message="Required numeric characters only.",
                            ),
                        ],
                    ),
                ),
                (
                    "card_number",
                    models.CharField(
                        max_length=22,
                        unique=True,
                        validators=[
                            django.core.validators.MinLengthValidator(1),
                            django.core.validators.MaxLengthValidator(22),
                            django.core.validators.RegexValidator(
                                regex="^\\d+$",
                                message="Required numeric characters only.",
                            ),
                        ],
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        max_length=16,
                        unique=True,
                        help_text="ex. +2920181234",
                        validators=[
                            django.core.validators.MinLengthValidator(1),
                            django.core.validators.MaxLengthValidator(16),
                            django.core.validators.RegexValidator(
                                regex="^\\+\\d+$",
                                message="Phone number must have +2920181234 format.",
                            ),
                        ],
                    ),
                ),
                (
                    "status",
                    ralph.lib.transitions.fields.TransitionField(
                        default=1,
                        choices=[
                            (1, "new"),
                            (2, "in progress"),
                            (3, "waiting for release"),
                            (4, "in use"),
                            (5, "damaged"),
                            (6, "liquidated"),
                            (7, "free"),
                            (8, "reserved"),
                            (9, "loan in progress"),
                            (10, "return in progress"),
                            (11, "in quarantine"),
                        ],
                    ),
                ),
                ("remarks", models.TextField(blank=True)),
                (
                    "quarantine_until",
                    models.DateField(
                        blank=True, null=True, help_text="End of quarantine date."
                    ),
                ),
                (
                    "carrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sim_cards.CellularCarrier",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        related_name="owned_simcards",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        related_name="used_simcards",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="back_office.Warehouse",
                    ),
                ),
            ],
            options={
                "ordering": ("-modified", "-created"),
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
    ]
