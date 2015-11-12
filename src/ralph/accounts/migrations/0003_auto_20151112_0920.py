# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150911_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ralphuser',
            name='regions',
            field=models.ManyToManyField(related_name='users', blank=True, to='accounts.Region'),
        ),
    ]
