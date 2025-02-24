# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import dj.choices.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ralph.access_cards.models
import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_remove_ralphuser_gender"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessCard",
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
                    "visual_number",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        help_text="Number visible on the access card",
                    ),
                ),
                (
                    "system_number",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        help_text="Internal number in the access system",
                    ),
                ),
                (
                    "issue_date",
                    models.DateField(
                        blank=True, null=True, help_text="Date of issue to the User"
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, null=True, help_text="Optional notes"),
                ),
                (
                    "status",
                    dj.choices.fields.ChoiceField(
                        default=1,
                        choices=ralph.access_cards.models.AccessCardStatus,
                        help_text="Access card status",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        help_text="Owner of the card",
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        to="accounts.Region",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        help_text="User of the card",
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
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
