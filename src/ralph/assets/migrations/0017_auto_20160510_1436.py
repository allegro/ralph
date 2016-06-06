# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0016_auto_20160429_1125'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='configurationmodule',
            name='path',
        ),
        migrations.RenameField(
            model_name='configurationclass',
            old_name='name',
            new_name='class_name',
        ),
        migrations.AlterField(
            model_name='configurationclass',
            name='path',
            field=models.TextField(blank=True, verbose_name='path', editable=False, help_text='path is constructed from name of module and name of class', default=''),
        ),
        migrations.AlterUniqueTogether(
            name='configurationclass',
            unique_together=set([('module', 'class_name')]),
        ),
    ]
