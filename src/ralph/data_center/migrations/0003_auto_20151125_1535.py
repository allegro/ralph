# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0001_initial'),
        ('supports', '0001_initial'),
        ('assets', '0002_auto_20151125_1354'),
        ('data_center', '0002_auto_20151125_1354'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CloudProject',
        ),
        migrations.DeleteModel(
            name='VirtualServer',
        ),
    ]
