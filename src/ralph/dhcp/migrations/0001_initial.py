# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0006_auto_20160404_0852'),
    ]

    operations = [
        migrations.CreateModel(
            name='DHCPServer',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('ip', models.IPAddressField(verbose_name='IP address', unique=True)),
                ('last_synchronized', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'DHCP Server',
                'verbose_name_plural': 'DHCP Servers',
            },
        ),
        migrations.CreateModel(
            name='DHCPEntry',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('networks.ipaddress',),
        ),
    ]
