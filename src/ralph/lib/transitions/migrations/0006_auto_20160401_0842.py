# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0005_auto_20160325_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='transition',
            name='run_asynchronously',
            field=models.BooleanField(default=False, help_text='Run this transition in the background (this could be enforced if you choose at least one asynchronous action)'),
        ),
        migrations.AlterField(
            model_name='transition',
            name='async_service_name',
            field=models.CharField(max_length=100, default='ASYNC_TRANSITIONS', blank=True, help_text='Name of asynchronous (internal) service to run this transition. Fill this field only if you want to run this transition in the background.', null=True),
        ),
    ]
