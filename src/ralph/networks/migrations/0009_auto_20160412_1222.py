# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0008_remove_ipaddress_base_object'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ipaddress',
            name='base_object',
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='ethernet',
            field=models.OneToOneField(to='assets.Ethernet', default=None, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='is_gateway',
            field=models.BooleanField(default=False, verbose_name='Is gateway address'),
        ),
        migrations.AlterField(
            model_name='network',
            name='dns_servers',
            field=models.ManyToManyField(verbose_name='DNS servers', to='dhcp.DNSServer', blank=True),
        ),
    ]
