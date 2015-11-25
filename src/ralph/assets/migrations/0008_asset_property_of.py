# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_auto_20151118_0804'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='property_of_2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, null=True, to='assets.AssetHolder', blank=True),
        ),
    ]
