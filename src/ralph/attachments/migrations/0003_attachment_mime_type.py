# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_auto_20150818_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='mime_type',
            field=models.CharField(default='application/octet-stream', max_length=100),
        ),
    ]
