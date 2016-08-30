# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0019_dchost'),
    ]

    operations = [
        migrations.AddField(
            model_name='vip',
            name='name',
            field=models.CharField(null=True, verbose_name='name', blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='vip',
            name='port',
            field=models.PositiveIntegerField(default=0, verbose_name='port'),
        ),
        migrations.AddField(
            model_name='vip',
            name='protocol',
            field=models.PositiveIntegerField(choices=[(1, 'unknown'), (2, 'TCP'), (3, 'HTTP')], default=1, verbose_name='protocol'),
        ),
    ]
