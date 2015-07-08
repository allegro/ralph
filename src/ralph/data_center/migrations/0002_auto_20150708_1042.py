# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        ('data_center', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudProjectType',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'cloud projects types',
                'ordering': ('name',),
                'verbose_name': 'cloud project type',
            },
        ),
        migrations.CreateModel(
            name='DatabaseType',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'databases types',
                'ordering': ('name',),
                'verbose_name': 'database type',
            },
        ),
        migrations.CreateModel(
            name='VIPType',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'VIPs types',
                'ordering': ('name',),
                'verbose_name': 'VIP type',
            },
        ),
        migrations.CreateModel(
            name='VirtualServerModel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, null=True, blank=True, to='assets.Manufacturer')),
            ],
            options={
                'verbose_name_plural': 'virtual servers types',
                'ordering': ('name',),
                'verbose_name': 'virtual server type',
            },
        ),
        migrations.AlterModelOptions(
            name='cloudproject',
            options={'verbose_name_plural': 'cloud projects', 'verbose_name': 'cloud project'},
        ),
        migrations.AddField(
            model_name='cloudproject',
            name='key',
            field=models.CharField(blank=True, verbose_name='key', unique=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='database',
            name='name',
            field=models.CharField(default=0, unique=True, max_length=255, verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='address',
            field=models.ForeignKey(default=0, to='data_center.IPAddress', verbose_name='address'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='name',
            field=models.CharField(default=0, unique=True, max_length=255, verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='port',
            field=models.PositiveIntegerField(default=0, verbose_name='port'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='protocol',
            field=models.PositiveIntegerField(default=1, choices=[(1, 'TCP'), (2, 'UDP')], verbose_name='protocol'),
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='hostname',
            field=models.CharField(default=None, blank=True, verbose_name='hostname', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='sn',
            field=models.CharField(blank=True, verbose_name='sn', unique=True, max_length=200, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='vip',
            unique_together=set([('address', 'port', 'protocol')]),
        ),
        migrations.AddField(
            model_name='cloudproject',
            name='cloud_project_type',
            field=models.ForeignKey(default=0, related_name='cloud_projects', to='data_center.CloudProjectType', verbose_name='cloud project type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='database',
            name='database_type',
            field=models.ForeignKey(default=0, related_name='databases', to='data_center.DatabaseType', verbose_name='database type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vip',
            name='vip_type',
            field=models.ForeignKey(default=0, related_name='vips', to='data_center.VIPType', verbose_name='VIP type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='virtualserver',
            name='model',
            field=models.ForeignKey(default=0, related_name='virtuals', to='data_center.VirtualServerModel', verbose_name='model'),
            preserve_default=False,
        ),
    ]
