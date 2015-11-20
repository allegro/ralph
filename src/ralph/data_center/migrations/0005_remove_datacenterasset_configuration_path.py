# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0004_auto_20151118_0916'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datacenterasset',
            name='configuration_path',
        ),
    ]
