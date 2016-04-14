# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_auto_20160405_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiskShareComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('share_id', models.PositiveIntegerField(blank=True, verbose_name='share identifier', null=True)),
                ('label', models.CharField(max_length=255, blank=True, null=True, verbose_name='name', default=None)),
                ('size', models.PositiveIntegerField(blank=True, verbose_name='size (MiB)', null=True)),
                ('snapshot_size', models.PositiveIntegerField(blank=True, verbose_name='size for snapshots (MiB)', null=True)),
                ('wwn', ralph.lib.mixins.fields.NullableCharField(max_length=33, unique=True, verbose_name='Volume serial')),
                ('full', models.BooleanField(default=True)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='disksharecomponent')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'disk shares',
                'verbose_name': 'disk share',
            },
        ),
        migrations.CreateModel(
            name='DiskShareMountComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('volume', models.CharField(max_length=255, blank=True, null=True, verbose_name='volume', default=None)),
                ('size', models.PositiveIntegerField(blank=True, verbose_name='size (MiB)', null=True)),
                ('asset', models.ForeignKey(blank=True, verbose_name='asset', null=True, to='assets.Asset', default=None, on_delete=django.db.models.deletion.SET_NULL)),
                ('share', models.ForeignKey(to='assets.DiskShareComponent', verbose_name='share')),
            ],
            options={
                'verbose_name_plural': 'disk share mounts',
                'verbose_name': 'disk share mount',
            },
        ),
        migrations.CreateModel(
            name='FibreChannelComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('physical_id', models.CharField(max_length=32, verbose_name='name')),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='fibrechannel')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'fibre channels',
                'verbose_name': 'fibre channel',
            },
        ),
        migrations.CreateModel(
            name='MemoryComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('size', models.PositiveIntegerField(blank=True, verbose_name='size (MiB)', null=True)),
                ('speed', models.PositiveIntegerField(blank=True, verbose_name='speed (MHz)', null=True)),
                ('index', models.PositiveIntegerField(blank=True, verbose_name='slot number', null=True)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='memory')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'memories',
                'verbose_name': 'memory',
            },
        ),
        migrations.CreateModel(
            name='OperatingSystemComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('memory', models.PositiveIntegerField(blank=True, help_text='in MiB', verbose_name='memory', null=True)),
                ('storage', models.PositiveIntegerField(blank=True, help_text='in MiB', verbose_name='storage', null=True)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='operatingsystem')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'operating systems',
                'verbose_name': 'operating system',
            },
        ),
        migrations.CreateModel(
            name='ProcessorComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('speed', models.PositiveIntegerField(blank=True, verbose_name='speed (MHz)', null=True)),
                ('cores', models.PositiveIntegerField(blank=True, verbose_name='number of cores', null=True)),
                ('index', models.PositiveIntegerField(blank=True, verbose_name='slot number', null=True)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='processor')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'processors',
                'verbose_name': 'processor',
            },
        ),
        migrations.CreateModel(
            name='SoftwareComponent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('sn', models.CharField(max_length=255, blank=True, verbose_name='vendor SN', default=None, null=True, unique=True)),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('path', models.CharField(max_length=255, blank=True, null=True, verbose_name='path', default=None)),
                ('version', models.CharField(max_length=255, blank=True, null=True, verbose_name='version', default=None)),
                ('base_object', models.ForeignKey(to='assets.BaseObject', related_name='software')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', null=True, to='assets.ComponentModel', default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name_plural': 'software',
                'verbose_name': 'software',
            },
        ),
        migrations.AlterUniqueTogether(
            name='disksharemountcomponent',
            unique_together=set([('share', 'asset')]),
        ),
    ]
