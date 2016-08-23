# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0019_dchost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cluster',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(unique=True, null=True, blank=True, max_length=255, db_index=True, verbose_name='hostname'),
        ),
    ]
