# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cross_validator', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='result',
            old_name='result',
            new_name='diff',
        ),
    ]
