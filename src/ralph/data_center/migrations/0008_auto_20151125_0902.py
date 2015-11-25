# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0007_auto_20151120_1210'),
    ]

    operations = [
        migrations.RenameField(
            model_name='diskshare',
            old_name='asset',
            new_name='base_object',
        ),
    ]
