# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0014_ipaddress_dhcp_expose'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='address',
            field=models.GenericIPAddressField(unique=True, verbose_name='IP address', help_text='Presented as string.'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, 'used (fixed address in DHCP)'), (2, 'reserved')], default=1),
        ),
        migrations.AlterField(
            model_name='networkenvironment',
            name='hostname_template_postfix',
            field=models.CharField(verbose_name='hostname template postfix', max_length=30, help_text='This value will be used as a postfix when generating new hostname in this network environment. For example, when prefix is "s1", postfix is ".mydc.net" and counter length is 4, following  hostnames will be generated: s10000.mydc.net, s10001.mydc.net, .., s19999.mydc.net.'),
        ),
    ]
