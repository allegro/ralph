# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhcp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DNSServer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('ip_address', models.IPAddressField(unique=True, verbose_name='IP address')),
                ('is_default', models.BooleanField(default=False, db_index=True, verbose_name='is default')),
            ],
            options={
                'verbose_name_plural': 'DNS Servers',
                'verbose_name': 'DNS Server',
            },
        ),
    ]
