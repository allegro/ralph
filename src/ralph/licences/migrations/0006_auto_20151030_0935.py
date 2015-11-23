# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0005_software_asset_type'),
        ('assets', '0005_assetholder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licence',
            name='property_of',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, null=True, to='assets.AssetHolder'),
        ),
    ]
