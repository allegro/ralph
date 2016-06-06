# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0009_auto_20160412_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='is_gateway',
            field=models.BooleanField(default=False, editable=False, verbose_name='Is gateway'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='is_public',
            field=models.BooleanField(default=False, editable=False, verbose_name='Is public'),
        ),
    ]
