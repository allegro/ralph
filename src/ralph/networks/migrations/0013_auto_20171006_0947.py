# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0012_remove_network_dns_servers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='dns_servers_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dhcp.DNSServerGroup', null=True, blank=True),
        ),
    ]
