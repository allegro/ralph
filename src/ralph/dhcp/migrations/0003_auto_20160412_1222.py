# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhcp', '0002_dnsserver'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dhcpserver',
            name='ip',
            field=models.GenericIPAddressField(verbose_name='IP address', unique=True),
        ),
        migrations.AlterField(
            model_name='dnsserver',
            name='ip_address',
            field=models.GenericIPAddressField(verbose_name='IP address', unique=True),
        ),
    ]
