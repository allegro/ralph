# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_marks', '0009_auto_20210630_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='design',
            name='classes',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='design',
            name='number',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='patent',
            name='classes',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='patent',
            name='number',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='trademark',
            name='classes',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='trademark',
            name='number',
            field=models.CharField(max_length=255),
        ),
    ]
