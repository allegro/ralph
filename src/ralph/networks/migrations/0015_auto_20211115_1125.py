# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0014_auto_20171009_1030"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ipaddress",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharFieldWithAutoStrip(
                verbose_name="hostname",
                max_length=255,
                blank=True,
                null=True,
                default=None,
            ),
        ),
    ]
