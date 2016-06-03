# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import re
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0018_auto_20160512_0842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernet',
            name='mac',
            field=ralph.lib.mixins.fields.NullableCharField(max_length=24, verbose_name='MAC address', null=True, validators=[django.core.validators.RegexValidator(regex=re.compile('^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$', 32), message="'%(value)s' is not a valid MAC address.")], blank=True, unique=True),
        ),
    ]
