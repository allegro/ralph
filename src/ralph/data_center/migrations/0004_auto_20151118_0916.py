# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0003_fix_ip_int'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipaddress',
            name='hostname',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Hostname', default=None),
        ),
    ]
