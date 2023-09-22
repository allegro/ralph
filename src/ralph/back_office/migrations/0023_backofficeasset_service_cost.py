# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0022_auto_20230616_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='backofficeasset',
            name='service_cost',
            field=models.IntegerField(verbose_name='Service Cost', default=None, null=True, blank=True),
        ),
    ]
