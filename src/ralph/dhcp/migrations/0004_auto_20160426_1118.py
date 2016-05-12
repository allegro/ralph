# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhcp', '0003_auto_20160412_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dhcpserver',
            name='last_synchronized',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
