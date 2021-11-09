# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields
import ralph.lib.field_validation.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0032_auto_20200909_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharFieldWithAutoStrip(verbose_name='hostname', max_length=255, blank=True, null=True, default=None, validators=[ralph.lib.field_validation.validators.HostnameValidator()]),
        ),
    ]
