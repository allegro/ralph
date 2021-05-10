# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0032_auto_20200909_1012'),
        ('accessories', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessory',
            name='accessory_type',
        ),
        migrations.AddField(
            model_name='accessory',
            name='category',
            field=mptt.fields.TreeForeignKey(null=True, related_name='+', to='assets.Category'),
        ),
        migrations.RemoveField(
            model_name='accessory',
            name='manufacturer'
        ),
        migrations.AddField(
            model_name='accessory',
            name='manufacturer',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    to='assets.Manufacturer'),
        ),
    ]
