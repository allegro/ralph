# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_auto_20150721_1223'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asset',
            old_name='deprecation_end_date',
            new_name='depreciation_end_date',
        ),
        migrations.RenameField(
            model_name='asset',
            old_name='deprecation_rate',
            new_name='depreciation_rate',
        ),
        migrations.RenameField(
            model_name='asset',
            old_name='force_deprecation',
            new_name='force_depreciation',
        ),
    ]
