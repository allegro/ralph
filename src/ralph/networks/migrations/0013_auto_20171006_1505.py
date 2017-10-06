# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0012_remove_network_dns_servers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='dns_servers_group',
            field=models.ForeignKey(null=True, related_name='networks', blank=True, to='dhcp.DNSServerGroup'),
        ),
    ]
