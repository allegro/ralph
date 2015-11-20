# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0006_auto_20151120_0829'),
    ]

    operations = [
        migrations.AddField(
            model_name='datacenterasset',
            name='management_hostname',
            field=ralph.lib.mixins.fields.NullableCharField(unique=True, max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='management_ip',
            field=models.GenericIPAddressField(help_text='Presented as string.', null=True, verbose_name='Management IP address', unique=True, default=None, blank=True),
        ),
    ]
