# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_marks', '0010_auto_20210630_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='design',
            name='database_link',
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='patent',
            name='database_link',
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trademark',
            name='database_link',
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
    ]
