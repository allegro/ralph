# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0011_auto_20160425_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='is_gateway',
            field=models.BooleanField(verbose_name='Is gateway', default=False),
        ),
        migrations.AlterField(
            model_name='networkenvironment',
            name='hostname_template_postfix',
            field=models.CharField(max_length=30, verbose_name='hostname template prefix', help_text='This value will be used as a postfix when generating new hostname in this network environment. For example, when prefix is "s1", postfix is ".mydc.net" and counter length is 4, following  hostnames will be generated: s10000.mydc.net, s10001.mydc.net, .., s19999.mydc.net.'),
        ),
    ]
