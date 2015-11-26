# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_auto_20151125_1354'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudFlavor',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, parent_link=True, primary_key=True, serialize=False, to='assets.BaseObject')),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
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
                ('baseobject_ptr', models.OneToOneField(auto_created=True, parent_link=True, primary_key=True, serialize=False, to='assets.BaseObject')),
                ('host_id', models.CharField(unique=True, max_length=100)),
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
                ('baseobject_ptr', models.OneToOneField(auto_created=True, parent_link=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
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
                ('baseobject_ptr', models.OneToOneField(auto_created=True, parent_link=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
            field=models.ForeignKey(verbose_name='model', blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='assets.ComponentModel'),
        ),
        migrations.AddField(
            model_name='cloudproject',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudflavor',
            name='cloudprovider',
            field=models.ForeignKey(to='virtual.CloudProvider'),
        ),
    ]
