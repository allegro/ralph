# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0008_auto_20160308_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='datacenter',
            name='show_on_dashboard',
            field=models.BooleanField(default=True),
        ),
    ]
