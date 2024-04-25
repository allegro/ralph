# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtual', '0013_auto_20190625_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cloudhost',
            name='hostname',
            field=models.CharField(verbose_name='hostname', max_length=255, db_index=True),
        ),
    ]
