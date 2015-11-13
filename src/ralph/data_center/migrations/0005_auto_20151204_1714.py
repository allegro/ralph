# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supports', '0003_auto_20151204_1325'),
        ('licences', '0002_auto_20151204_1325'),
        ('assets', '0004_auto_20151204_0758'),
        ('data_center', '0004_auto_20151204_0758'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CloudProject',
        ),
        migrations.DeleteModel(
            name='VirtualServer',
        ),
    ]
