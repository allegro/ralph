# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0012_auto_20160316_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='diskshare',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='date created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='diskshare',
            name='modified',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name='last modified'),
            preserve_default=False,
        ),
    ]
