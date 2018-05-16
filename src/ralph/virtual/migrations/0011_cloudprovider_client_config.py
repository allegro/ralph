# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_cryptography.fields


class Migration(migrations.Migration):

    dependencies = [
        ('virtual', '0010_auto_20181018_0822'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudprovider',
            name='client_config',
            field=django_cryptography.fields.encrypt(models.TextField(blank=True, verbose_name='client configuration', null=True)),
        ),
    ]
