# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import re
import ralph.lib.mixins.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0018_auto_20160512_0842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(verbose_name='hostname', default=None, blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='ethernet',
            name='mac',
            field=ralph.lib.mixins.fields.NullableCharField(unique=True, max_length=24, verbose_name='MAC address', blank=True, null=True, validators=[django.core.validators.RegexValidator(message="'%(value)s' is not a valid MAC address.", regex=re.compile('^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$', 32))]),
        ),
    ]
