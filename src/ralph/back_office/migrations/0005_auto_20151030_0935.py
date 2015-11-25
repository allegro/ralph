# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0006_auto_20151030_0935'),
        ('back_office', '0004_auto_20151023_1308'),
        ('assets', '0005_assetholder')
    ]

    operations = [
        migrations.AlterField(
            model_name='backofficeasset',
            name='property_of',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, null=True, to='assets.AssetHolder'),
        ),
        migrations.DeleteModel(
            name='AssetHolder',
        ),
    ]
