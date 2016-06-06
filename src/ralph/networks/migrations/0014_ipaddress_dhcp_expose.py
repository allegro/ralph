# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0013_auto_20160509_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipaddress',
            name='dhcp_expose',
            field=models.BooleanField(default=False, verbose_name='Expose in DHCP'),
        ),
    ]
