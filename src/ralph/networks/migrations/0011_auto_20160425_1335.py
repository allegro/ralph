# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0010_auto_20160420_0928'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='networkenvironment',
            name='hosts_naming_template',
        ),
        migrations.AddField(
            model_name='networkenvironment',
            name='hostname_template_counter_length',
            field=models.PositiveIntegerField(default=4, verbose_name='hostname template counter length'),
        ),
        migrations.AddField(
            model_name='networkenvironment',
            name='hostname_template_postfix',
            field=models.CharField(max_length=30, help_text='This value will be used as a postfix when generating new hostname in this network environment. For example, when prefix is "s1", postfix is ".mydc.net" and counter length is 4, following  hostnames will be generated: s10000.mydc.net, s10001.mydc.net, ..., s19999.mydc.net.', verbose_name='hostname template prefix', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='networkenvironment',
            name='hostname_template_prefix',
            field=models.CharField(max_length=30, verbose_name='hostname template prefix', default=''),
            preserve_default=False,
        ),
    ]
