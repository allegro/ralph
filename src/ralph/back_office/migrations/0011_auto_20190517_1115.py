# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0010_backofficeasset_imei2"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backofficeasset",
            name="imei",
            field=ralph.lib.mixins.fields.NullableCharField(
                verbose_name="IMEI", max_length=18, unique=True, blank=True, null=True
            ),
        ),
        migrations.AlterField(
            model_name="backofficeasset",
            name="imei2",
            field=ralph.lib.mixins.fields.NullableCharField(
                verbose_name="IMEI 2", max_length=18, unique=True, blank=True, null=True
            ),
        ),
    ]
