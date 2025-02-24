# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0008_auto_20160808_0719"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ipaddress",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharField(
                null=True,
                blank=True,
                verbose_name="hostname",
                default=None,
                max_length=255,
            ),
        ),
    ]
