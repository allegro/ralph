# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150813_1252'),
        ('back_office', '0002_auto_20150805_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='backofficeasset',
            name='region',
            field=models.ForeignKey(to='accounts.Region', default=1),
            preserve_default=False,
        ),
    ]
