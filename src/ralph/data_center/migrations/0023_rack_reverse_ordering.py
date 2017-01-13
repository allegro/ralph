# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0022_auto_20161206_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='reverse_ordering',
            field=models.BooleanField(
                help_text=(
                    'Check if RU numbers count from top to bottom with '
                    'position 1 starting at the top of the rack. If '
                    'unchecked position 1is at the bottom of the rack'
                ),
                default=False,
                verbose_name='RU order top to bottom',
            ),
        ),
    ]
