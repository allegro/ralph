# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supports', '0005_auto_20160105_1222'),
        ('assets', '0008_auto_20160122_1429'),
        ('licences', '0002_auto_20151204_1325'),
        ('data_center', '0006_rack_require_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cloudproject',
            name='baseobject_ptr',
        ),
        migrations.RemoveField(
            model_name='virtualserver',
            name='baseobject_ptr',
        ),
        migrations.DeleteModel(
            name='CloudProject',
        ),
        migrations.DeleteModel(
            name='VirtualServer',
        ),
    ]
