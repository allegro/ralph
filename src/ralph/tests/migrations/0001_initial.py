# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.models
import ralph.lib.transitions.fields


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Car",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("year", models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="Foo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                ("bar", models.CharField(max_length=50, verbose_name="bar")),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Manufacturer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("country", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    ralph.lib.transitions.fields.TransitionField(
                        choices=[(1, "new"), (2, "to_send"), (3, "sended")], default=1
                    ),
                ),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="TestAsset",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                ("hostname", models.CharField(max_length=50)),
                (
                    "sn",
                    models.CharField(
                        unique=True, blank=True, null=True, max_length=200
                    ),
                ),
                (
                    "barcode",
                    models.CharField(
                        unique=True, blank=True, null=True, default=None, max_length=200
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="car",
            name="manufacturer",
            field=models.ForeignKey(
                to="tests.Manufacturer", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.CreateModel(
            name="BaseObjectForeignKeyModel",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "base_object",
                    ralph.lib.mixins.fields.BaseObjectForeignKey(
                        verbose_name="Asset",
                        related_name="licences",
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
    ]
