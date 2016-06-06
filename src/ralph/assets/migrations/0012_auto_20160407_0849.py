# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0011_auto_20160404_0852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernet',
            name='speed',
            field=models.PositiveIntegerField(choices=[(1, '10 Mbps'), (2, '100 Mbps'), (3, '1 Gbps'), (4, '10 Gbps'), (5, '40 Gbps'), (6, '100 Gbps'), (11, 'unknown speed')], default=11, verbose_name='speed'),
        ),
    ]
