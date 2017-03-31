# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0024_auto_20170322_1148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assets.AssetModel', related_name='assets'),
        ),
    ]
