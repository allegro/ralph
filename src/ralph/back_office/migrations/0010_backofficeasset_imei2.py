# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0009_auto_20181016_1252"),
    ]

    operations = [
        migrations.AddField(
            model_name="backofficeasset",
            name="imei2",
            field=ralph.lib.mixins.fields.NullableCharField(
                max_length=18, unique=True, blank=True, null=True
            ),
        ),
    ]
