# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0025_auto_20170510_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(null=True, to='data_center.Rack', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
