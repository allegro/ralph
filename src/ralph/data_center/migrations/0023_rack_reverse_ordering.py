# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0022_auto_20161206_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='reverse_ordering',
            field=models.BooleanField(help_text='Check if RU starts counting from top to bottom. Unchecked rack diagrams will start counting with 1 at the bottom', verbose_name='RU order top to bottom', default=settings.RACK_LISTING_NUMBERING_TOP_TO_BOTTOM),
        ),
    ]
