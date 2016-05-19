# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0009_auto_20160419_1003'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datacenter',
            name='visualization_cols_num',
        ),
        migrations.RemoveField(
            model_name='datacenter',
            name='visualization_rows_num',
        ),
        migrations.AddField(
            model_name='serverroom',
            name='visualization_cols_num',
            field=models.PositiveIntegerField(verbose_name='visualization grid columns number', default=20),
        ),
        migrations.AddField(
            model_name='serverroom',
            name='visualization_rows_num',
            field=models.PositiveIntegerField(verbose_name='visualization grid rows number', default=20),
        ),
    ]
