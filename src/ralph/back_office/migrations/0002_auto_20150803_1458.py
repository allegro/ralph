# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.transitions.fields


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backofficeasset',
            options={'verbose_name_plural': 'Back Office Assets', 'verbose_name': 'Back Office Asset'},
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='status',
            field=ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')]),
        ),
    ]
