# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securityscan',
            name='created',
            field=models.DateTimeField(verbose_name='date created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='securityscan',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified'),
        ),
        migrations.AlterField(
            model_name='vulnerability',
            name='created',
            field=models.DateTimeField(verbose_name='date created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='vulnerability',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified'),
        ),
    ]
