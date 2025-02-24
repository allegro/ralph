# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0014_memory"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="memory",
            options={"verbose_name": "memory", "verbose_name_plural": "memory"},
        ),
        migrations.RemoveField(
            model_name="memory",
            name="label",
        ),
        migrations.RemoveField(
            model_name="memory",
            name="slot_no",
        ),
        migrations.AddField(
            model_name="ethernet",
            name="firmware_version",
            field=models.CharField(
                max_length=255, verbose_name="firmware version", blank=True, null=True
            ),
        ),
        migrations.AddField(
            model_name="ethernet",
            name="model_name",
            field=models.CharField(
                max_length=255, verbose_name="model name", blank=True, null=True
            ),
        ),
        migrations.AddField(
            model_name="genericcomponent",
            name="model_name",
            field=models.CharField(
                max_length=255, verbose_name="model name", blank=True, null=True
            ),
        ),
        migrations.AddField(
            model_name="memory",
            name="model_name",
            field=models.CharField(
                max_length=255, verbose_name="model name", blank=True, null=True
            ),
        ),
        migrations.AlterField(
            model_name="ethernet",
            name="label",
            field=ralph.lib.mixins.fields.NullableCharField(
                max_length=255, verbose_name="label", blank=True, null=True
            ),
        ),
    ]
