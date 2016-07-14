# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0016_fibrechannelcard'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disk',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('model_name', models.CharField(blank=True, null=True, verbose_name='model name', max_length=255)),
                ('size', models.PositiveIntegerField(verbose_name='size (GiB)')),
                ('serial_number', models.CharField(blank=True, null=True, verbose_name='serial number', max_length=255)),
                ('slot', models.PositiveIntegerField(blank=True, null=True, verbose_name='slot number')),
                ('firmware_version', models.CharField(blank=True, null=True, verbose_name='firmware version', max_length=255)),
                ('base_object', models.ForeignKey(related_name='disk_set', to='assets.BaseObject')),
                ('model', models.ForeignKey(verbose_name='model', to='assets.ComponentModel', blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name': 'disk',
                'verbose_name_plural': 'disks',
            },
        ),
    ]
