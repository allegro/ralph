# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0002_auto_20150715_0752'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rackaccessory',
            options={'verbose_name_plural': 'rack accessories'},
        ),
    ]
