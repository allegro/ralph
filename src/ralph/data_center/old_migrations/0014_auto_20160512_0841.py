# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.transitions.fields
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0013_auto_20160404_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(verbose_name='hostname', unique=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='cluster',
            name='status',
            field=ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'in use'), (2, 'liquidated')]),
        ),
        migrations.AddField(
            model_name='clustertype',
            name='show_master_summary',
            field=models.BooleanField(default=False, help_text='show master information on cluster page, ex. hostname, model, location etc.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cluster',
            name='name',
            field=models.CharField(verbose_name='name', null=True, max_length=255, blank=True),
        ),
    ]
