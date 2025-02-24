# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0026_auto_20170510_0840"),
    ]

    operations = [
        migrations.CreateModel(
            name="SCMStatusCheck",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
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
                ("last_checked", models.DateTimeField(verbose_name="Last SCM check")),
                (
                    "check_result",
                    models.PositiveIntegerField(
                        choices=[(1, "OK"), (2, "Check failed"), (3, "Error")],
                        verbose_name="SCM check result",
                    ),
                ),
                (
                    "base_object",
                    models.OneToOneField(
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
