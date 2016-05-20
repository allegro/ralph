# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.transitions.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0014_auto_20160512_0841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cluster',
            name='status',
            field=ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'in use'), (2, 'for deploy')]),
        ),
        migrations.AlterField(
            model_name='clustertype',
            name='show_master_summary',
            field=models.BooleanField(default=False, help_text='show master information on cluster page, ex. hostname, model, location etc.'),
        ),
    ]
