# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0004_network_service_env'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='is_gateway',
            field=models.BooleanField(default=False, editable=False, verbose_name='Is gateway address'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='is_management',
            field=models.BooleanField(default=False, verbose_name='Is management address'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='is_public',
            field=models.BooleanField(default=False, editable=False, verbose_name='Is public address'),
        ),
    ]
