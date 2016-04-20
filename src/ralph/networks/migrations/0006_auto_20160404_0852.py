# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0011_auto_20160404_0852'),
        ('networks', '0005_auto_20160323_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipaddress',
            name='ethernet',
            field=models.OneToOneField(blank=True, null=True, default=None, on_delete=django.db.models.deletion.SET_NULL, to='assets.Ethernet'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='is_gateway',
            field=models.BooleanField(default=False, verbose_name='This is a gateway address'),
        ),
    ]
