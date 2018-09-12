# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('trade_marks', '0002_auto_20180912_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trademarks',
            name='tm_holder',
            field=models.ForeignKey(default=datetime.datetime(2018, 9, 12, 15, 36, 25, 900990), blank=True, verbose_name='Trade Mark holder', to='assets.AssetHolder'),
            preserve_default=False,
        ),
    ]
