# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtual', '0002_auto_20151223_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudhost',
            name='image_name',
            field=models.CharField(blank=True, null=True, max_length=255),
        ),
    ]
