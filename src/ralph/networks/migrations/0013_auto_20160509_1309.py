# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0012_auto_20160428_1259'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='networkenvironment',
            name='dhcp_next_server',
        ),
        migrations.AddField(
            model_name='networkenvironment',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date created', default=datetime.datetime(2016, 5, 9, 13, 9, 30, 432931)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='networkenvironment',
            name='modified',
            field=models.DateTimeField(verbose_name='last modified', default=datetime.datetime(2016, 5, 9, 13, 9, 32, 672831), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='networkenvironment',
            name='domain',
            field=ralph.lib.mixins.fields.NullableCharField(help_text='Used in DHCP configuration.', verbose_name='domain', blank=True, max_length=255, null=True),
        ),
    ]
