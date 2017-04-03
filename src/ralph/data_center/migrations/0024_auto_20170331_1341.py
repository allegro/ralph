# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0023_rack_reverse_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, blank=True, to='data_center.Rack'),
        ),
    ]
