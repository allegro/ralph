# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_asyncorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='remarks',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
    ]
