# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0014_auto_20160414_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetlasthostname',
            name='postfix',
            field=models.CharField(max_length=30, db_index=True),
        ),
        migrations.AlterField(
            model_name='assetlasthostname',
            name='prefix',
            field=models.CharField(max_length=30, db_index=True),
        ),
    ]
