# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150911_1159'),
        ('assets', '0002_category_imei_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='profitcenter',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='service',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='service',
            name='support_team',
            field=models.ForeignKey(to='accounts.Team', blank=True, null=True, related_name='services'),
        ),
    ]
