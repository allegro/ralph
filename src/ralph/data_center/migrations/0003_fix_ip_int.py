# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0002_auto_20151014_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='gateway_as_int',
            field=models.BigIntegerField(verbose_name='gateway as int', blank=True, default=None, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='network',
            name='max_ip',
            field=models.BigIntegerField(verbose_name='largest IP number', blank=True, default=None, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='network',
            name='min_ip',
            field=models.BigIntegerField(verbose_name='smallest IP number', blank=True, default=None, null=True, editable=False),
        ),
    ]
