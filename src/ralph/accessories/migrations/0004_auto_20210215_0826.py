# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accessories', '0003_auto_20210210_1147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessories',
            name='manufacturer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='assets.Manufacturer'),
        ),
    ]
