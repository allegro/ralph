# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0009_auto_20160823_0921'),
        ('data_center', '0019_dchost'),
    ]

    operations = [
        migrations.AddField(
            model_name='vip',
            name='ip',
            field=models.ForeignKey(default=None, to='networks.IPAddress', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vip',
            name='name',
            field=models.CharField(verbose_name='name', null=True, max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='vip',
            name='port',
            field=models.PositiveIntegerField(verbose_name='port', default=0),
        ),
        migrations.AddField(
            model_name='vip',
            name='protocol',
            field=models.PositiveIntegerField(verbose_name='protocol', default=1, choices=[(1, 'unknown'), (2, 'TCP'), (3, 'HTTP')]),
        ),
        migrations.AlterUniqueTogether(
            name='vip',
            unique_together=set([('ip', 'port', 'protocol')]),
        ),
    ]
