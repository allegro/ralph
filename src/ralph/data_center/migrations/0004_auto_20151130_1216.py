# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_auto_20151126_2205'),
        ('licences', '0001_initial'),
        ('supports', '0001_initial'),
        ('data_center', '0003_auto_20151126_2222'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CloudProject',
        ),
        migrations.DeleteModel(
            name='VirtualServer',
        ),
    ]
