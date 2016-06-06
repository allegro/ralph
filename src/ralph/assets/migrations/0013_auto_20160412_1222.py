# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0012_auto_20160407_0849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernet',
            name='label',
            field=models.CharField(max_length=255, verbose_name='name', blank=True),
        ),
        migrations.AlterField(
            model_name='ethernet',
            name='mac',
            field=models.CharField(verbose_name='MAC address', blank=True, null=True, max_length=24, unique=True, validators=[django.core.validators.RegexValidator(message="'%(value)s' is not a valid MAC address.", regex=re.compile('^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$', 32))]),
        ),
    ]
