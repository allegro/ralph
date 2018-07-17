# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0005_auto_20170523_1214'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalService',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
                'ordering': ['name'],
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.AddField(
            model_name='domain',
            name='additional_services',
            field=models.ManyToManyField(blank=True, to='domains.AdditionalService'),
        ),
    ]
