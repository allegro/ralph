# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0002_auto_20151125_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vulnerability',
            name='name',
            field=models.CharField(verbose_name='name', max_length=255),
        ),
    ]
