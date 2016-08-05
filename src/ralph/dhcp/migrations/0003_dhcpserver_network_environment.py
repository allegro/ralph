# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0007_auto_20160804_1409'),
        ('dhcp', '0002_dhcpentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='dhcpserver',
            name='network_environment',
            field=models.ForeignKey(to='networks.NetworkEnvironment', null=True, blank=True, default=None),
            preserve_default=False,
        ),
    ]
