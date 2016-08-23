# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0009_auto_20160823_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(default=None, db_index=True, max_length=255, blank=True, null=True, verbose_name='hostname'),
        ),
    ]
