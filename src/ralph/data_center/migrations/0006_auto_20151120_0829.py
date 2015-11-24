# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0005_remove_datacenterasset_configuration_path'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ipaddress',
            name='asset'
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='base_object',
            field=models.ForeignKey(
                to='assets.BaseObject',
                default=None,
                verbose_name='Base object',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True
            ),
        ),
    ]
