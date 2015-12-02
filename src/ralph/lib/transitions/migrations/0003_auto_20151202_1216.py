# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0002_auto_20151125_1354'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'ordering': ['name']},
        ),
    ]
