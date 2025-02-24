# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportedObjects",
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
                ("object_pk", models.IntegerField(db_index=True)),
                ("old_object_pk", models.CharField(db_index=True, max_length=255)),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
                "ordering": ("-modified", "-created"),
            },
        ),
    ]
