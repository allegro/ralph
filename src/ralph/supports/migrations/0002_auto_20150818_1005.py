# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150813_1252'),
        ('supports', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='support',
            name='additional_notes',
        ),
        migrations.AddField(
            model_name='support',
            name='region',
            field=models.ForeignKey(to='accounts.Region', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='support',
            name='remarks',
            field=models.TextField(blank=True),
        ),
    ]
