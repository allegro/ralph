# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0006_auto_20170719_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='transition',
            name='template_name',
            field=models.CharField(default='', max_length=255, blank=True),
        ),
    ]
