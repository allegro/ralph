# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0009_auto_20160307_1138'),
        ('networks', '0003_auto_20160322_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='service_env',
            field=models.ForeignKey(to='assets.ServiceEnvironment', related_name='networks', blank=True, default=None, null=True),
        ),
    ]
