# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0022_auto_20160823_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(null=True, blank=True, default=None, max_length=255, db_index=True, verbose_name='hostname'),
        ),
    ]
