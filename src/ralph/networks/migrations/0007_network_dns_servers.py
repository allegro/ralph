# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhcp', '0002_dnsserver'),
        ('networks', '0006_auto_20160404_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='dns_servers',
            field=models.ManyToManyField(blank=True, to='dhcp.DNSServer', null=True, verbose_name='DNS servers'),
        ),
    ]
