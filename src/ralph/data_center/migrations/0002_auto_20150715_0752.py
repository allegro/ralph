# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ipaddress',
            name='hostname',
        ),
        migrations.RemoveField(
            model_name='ipaddress',
            name='network',
        ),
    ]
