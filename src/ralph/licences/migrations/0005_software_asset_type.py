# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0004_auto_20151029_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='software',
            name='asset_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], default=4),
        ),
    ]
