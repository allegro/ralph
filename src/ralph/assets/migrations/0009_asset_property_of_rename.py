# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0008_asset_property_of'),
        ('back_office', '0007_copy_property_of'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asset',
            old_name='property_of_2',
            new_name='property_of'
        ),
    ]
