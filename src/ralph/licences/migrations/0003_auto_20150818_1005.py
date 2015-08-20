# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150813_1252'),
        ('licences', '0002_auto_20150807_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='licence',
            name='region',
            field=models.ForeignKey(to='accounts.Region', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='licence',
            name='remarks',
            field=models.TextField(blank=True),
        ),
    ]
