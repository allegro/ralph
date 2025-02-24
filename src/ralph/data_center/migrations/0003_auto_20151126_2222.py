# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0002_auto_20151125_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datacenterasset",
            name="management_ip",
            field=ralph.lib.mixins.fields.NullableGenericIPAddressField(
                blank=True,
                null=True,
                unique=True,
                default=None,
                help_text="Presented as string.",
                verbose_name="Management IP address",
            ),
        ),
        migrations.AlterField(
            model_name="datacenterasset",
            name="position",
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="datacenterasset",
            name="rack",
            field=models.ForeignKey(
                null=True,
                to="data_center.Rack",
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
