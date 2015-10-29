# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0004_auto_20151023_1308'),
        ('licences', '0002_licence_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='licence',
            name='property_of',
            field=models.ForeignKey(to='back_office.AssetHolder', null=True, on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
    ]
