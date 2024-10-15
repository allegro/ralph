# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0034_auto_20240304_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharFieldWithAutoStrip(verbose_name='hostname', max_length=255, blank=True, null=True, db_index=True, default=None),
        ),
    ]
