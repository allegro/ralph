# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_auto_20150721_1402'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='status',
        ),
    ]
