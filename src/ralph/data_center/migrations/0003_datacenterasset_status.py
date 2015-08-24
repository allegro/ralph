# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.transitions.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0002_auto_20150715_0752'),
    ]

    operations = [
        migrations.AddField(
            model_name='datacenterasset',
            name='status',
            field=ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')]),
        ),
    ]
