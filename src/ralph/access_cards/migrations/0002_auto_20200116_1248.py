# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import mptt.fields
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("access_cards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessZone",
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
                ("name", models.CharField(verbose_name="name", max_length=255)),
                (
                    "description",
                    models.TextField(
                        blank=True, null=True, help_text="Optional description"
                    ),
                ),
                ("lft", models.PositiveIntegerField(db_index=True, editable=False)),
                ("rght", models.PositiveIntegerField(db_index=True, editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(db_index=True, editable=False)),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        blank=True,
                        null=True,
                        related_name="children",
                        to="access_cards.AccessZone",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.AddField(
            model_name="accesscard",
            name="access_zones",
            field=mptt.fields.TreeManyToManyField(
                blank=True, related_name="access_cards", to="access_cards.AccessZone"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="accesszone",
            unique_together=set([("name", "parent")]),
        ),
    ]
