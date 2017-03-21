# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0003_auto_20170110_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='securityscan',
            name='last_security_scan',
            field=models.OneToOneField(to='security.SecurityScan', blank=True, null=True),
        ),
    ]
