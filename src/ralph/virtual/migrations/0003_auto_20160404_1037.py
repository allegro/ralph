# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('virtual', '0002_auto_20160226_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualcomponent',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date created', default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='virtualcomponent',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified', default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
