# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0013_auto_20160404_0852'),
        ('virtual', '0003_auto_20160404_1037'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualServerType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='cluster',
            field=models.ForeignKey(to='data_center.Cluster', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(verbose_name='hostname', null=True, default=None, max_length=255, blank=True, unique=True),
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='sn',
            field=models.CharField(verbose_name='SN', max_length=200, default=1, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='type',
            field=models.ForeignKey(to='virtual.VirtualServerType', related_name='virtual_servers', default=1),
            preserve_default=False,
        ),
    ]
