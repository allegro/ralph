# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0008_auto_20160122_1429'),
        ('data_center', '0007_auto_20160225_1818'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudFlavor',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, to='assets.BaseObject', serialize=False, parent_link=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=255)),
                ('flavor_id', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='CloudHost',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, to='assets.BaseObject', serialize=False, parent_link=True, auto_created=True)),
                ('host_id', models.CharField(unique=True, max_length=100)),
                ('hostname', models.CharField(max_length=100)),
                ('image_name', models.CharField(max_length=255, null=True, blank=True)),
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
                ('baseobject_ptr', models.OneToOneField(primary_key=True, to='assets.BaseObject', serialize=False, parent_link=True, auto_created=True)),
                ('project_id', models.CharField(unique=True, max_length=100)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Cloud provider',
                'verbose_name_plural': 'Cloud providers',
            },
        ),
        migrations.CreateModel(
            name='VirtualComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, to='assets.BaseObject', serialize=False, parent_link=True, auto_created=True)),
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
            field=models.ForeignKey(to='assets.BaseObject', related_name='virtualcomponent'),
        ),
        migrations.AddField(
            model_name='virtualcomponent',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='assets.ComponentModel', null=True, verbose_name='model', default=None, blank=True),
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
            field=models.ForeignKey(to='data_center.DataCenterAsset', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='cloudflavor',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
    ]
