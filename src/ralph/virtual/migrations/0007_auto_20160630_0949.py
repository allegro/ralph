# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("virtual", "0006_virtualcomponent_model_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="virtualserver",
            name="sn",
            field=ralph.lib.mixins.fields.NullableCharField(
                max_length=200,
                null=True,
                blank=True,
                verbose_name="SN",
                default=None,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="virtualservertype",
            name="name",
            field=models.CharField(verbose_name="name", max_length=255, unique=True),
        ),
    ]
