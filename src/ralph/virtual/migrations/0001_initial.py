# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_auto_20151204_0758'),
        ('data_center', '0005_auto_20151204_1714'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudFlavor',
            fields=[
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
                ('host_id', models.CharField(max_length=100, unique=True)),
                ('hostname', models.CharField(max_length=100)),
                ('cloudflavor', models.ForeignKey(verbose_name='Instance Type', to='virtual.CloudFlavor')),
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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'verbose_name': 'Cloud provider',
                'verbose_name_plural': 'Cloud providers',
            },
        ),
        migrations.CreateModel(
            name='VirtualComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='model', null=True, to='assets.ComponentModel', blank=True, default=None),
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
            field=models.ForeignKey(null=True, to='data_center.DataCenterAsset', blank=True),
        ),
        migrations.AddField(
            model_name='cloudflavor',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
    ]
