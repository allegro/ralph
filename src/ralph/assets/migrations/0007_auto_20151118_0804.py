# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0006_auto_20151110_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetmodel',
            name='cores_count',
            field=models.PositiveIntegerField(default=0, blank=True, verbose_name='Cores count'),
        ),
        migrations.AlterField(
            model_name='assetmodel',
            name='height_of_device',
            field=models.FloatField(default=0, blank=True, verbose_name='Height of device', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='assetmodel',
            name='power_consumption',
            field=models.PositiveIntegerField(default=0, blank=True, verbose_name='Power consumption'),
        ),
    ]
