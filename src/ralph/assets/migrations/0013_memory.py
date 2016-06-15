# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0012_auto_20160606_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)')),
                ('speed', models.PositiveIntegerField(blank=True, verbose_name='speed (MHz)', null=True)),
                ('slot_no', models.PositiveIntegerField(blank=True, verbose_name='slot number', null=True)),
                ('base_object', models.ForeignKey(related_name='memory_set', to='assets.BaseObject')),
                ('model', models.ForeignKey(to='assets.ComponentModel', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='model')),
            ],
            options={
                'verbose_name_plural': 'memories',
                'verbose_name': 'memory',
            },
        ),
    ]
