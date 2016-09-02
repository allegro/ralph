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
            field=models.ForeignKey(to='networks.IPAddress', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='port',
            field=models.PositiveIntegerField(verbose_name='port', default=0),
        ),
        migrations.AddField(
            model_name='vip',
            name='protocol',
            field=models.PositiveIntegerField(choices=[(1, 'TCP'), (2, 'UDP')], verbose_name='protocol', default=1),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='vip',
            unique_together=set([('ip', 'port', 'protocol')]),
        ),
    ]
