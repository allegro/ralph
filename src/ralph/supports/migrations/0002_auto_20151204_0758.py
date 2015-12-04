# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supports', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supporttype',
            options={'ordering': ['name']},
        ),
    ]
