# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import re
import ralph.lib.mixins.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0018_disk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernet',
            name='mac',
            field=ralph.lib.mixins.fields.MACAddressField(blank=True, null=True, verbose_name='MAC address', unique=True, validators=[django.core.validators.RegexValidator(regex=re.compile('^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$', 32), message="'%(value)s' is not a valid MAC address.")]),
        ),
    ]
