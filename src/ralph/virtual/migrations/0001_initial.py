# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_auto_20151126_2205'),
        ('data_center', '0004_auto_20151130_1216'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudFlavor',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('flavor_id', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='CloudHost',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True)),
                ('host_id', models.CharField(max_length=100, unique=True)),
                ('hostname', models.CharField(max_length=100)),
                ('cloudflavor', models.ForeignKey(to='virtual.CloudFlavor', verbose_name='Instance Type')),
            ],
            options={
                'verbose_name': 'Cloud host',
                'verbose_name_plural': 'Cloud hosts',
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='CloudProject',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True)),
                ('project_id', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='CloudProvider',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Cloud provider',
                'verbose_name_plural': 'Cloud providers',
            },
        ),
        migrations.CreateModel(
            name='VirtualComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True)),
            ],
            options={
                'verbose_name': 'Virtual server (VM)',
                'verbose_name_plural': 'Virtual servers (VM)',
            },
            bases=('assets.baseobject',),
        ),
        migrations.AddField(
            model_name='virtualcomponent',
            name='base_object',
            field=models.ForeignKey(related_name='virtualcomponent', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='virtualcomponent',
            name='model',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.SET_NULL, to='assets.ComponentModel', verbose_name='model', null=True),
        ),
        migrations.AddField(
            model_name='cloudproject',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudhost',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudhost',
            name='hypervisor',
            field=models.ForeignKey(blank=True, to='data_center.DataCenterAsset', null=True),
        ),
        migrations.AddField(
            model_name='cloudflavor',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
    ]
