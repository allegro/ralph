# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
            ],
            options={
                'verbose_name': 'accessory',
                'verbose_name_plural': 'accessories',
            },
        ),
        migrations.CreateModel(
            name='CloudProject',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('connection_type', models.PositiveIntegerField(verbose_name='connection type', choices=[(1, 'network connection')])),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
            ],
            options={
                'verbose_name': 'database',
                'verbose_name_plural': 'databases',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='DataCenter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('visualization_cols_num', models.PositiveIntegerField(default=20, verbose_name='visualization grid columns number')),
                ('visualization_rows_num', models.PositiveIntegerField(default=20, verbose_name='visualization grid rows number')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataCenterAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
                ('niw', models.CharField(default=None, max_length=200, null=True, verbose_name='Inventory number', blank=True)),
                ('invoice_no', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('required_support', models.BooleanField(default=False)),
                ('order_no', models.CharField(max_length=50, null=True, blank=True)),
                ('purchase_order', models.CharField(max_length=50, null=True, blank=True)),
                ('invoice_date', models.DateField(null=True, blank=True)),
                ('sn', models.CharField(max_length=200, unique=True, null=True, blank=True)),
                ('barcode', models.CharField(default=None, max_length=200, unique=True, null=True, blank=True)),
                ('price', models.DecimalField(default=0, null=True, max_digits=10, decimal_places=2, blank=True)),
                ('provider', models.CharField(max_length=100, null=True, blank=True)),
                ('source', models.PositiveIntegerField(blank=True, null=True, verbose_name='source', db_index=True, choices=[(1, 'shipment'), (2, 'salvaged')])),
                ('status', models.PositiveSmallIntegerField(default=1, null=True, verbose_name='status', blank=True, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')])),
                ('request_date', models.DateField(null=True, blank=True)),
                ('delivery_date', models.DateField(null=True, blank=True)),
                ('production_use_date', models.DateField(null=True, blank=True)),
                ('provider_order_date', models.DateField(null=True, blank=True)),
                ('deprecation_rate', models.DecimalField(default=25, help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .', max_digits=5, decimal_places=2, blank=True)),
                ('force_deprecation', models.BooleanField(help_text='Check if you no longer want to bill for this asset')),
                ('deprecation_end_date', models.DateField(null=True, blank=True)),
                ('production_year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('task_url', models.URLField(help_text='External workflow system URL', max_length=2048, null=True, blank=True)),
                ('loan_end_date', models.DateField(default=None, null=True, verbose_name='Loan end date', blank=True)),
                ('slots', models.FloatField(default=0, help_text=b'For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', max_length=64, verbose_name=b'Slots')),
                ('slot_no', models.CharField(help_text='Fill it if asset is blade server', max_length=3, null=True, verbose_name='slot number', blank=True)),
                ('configuration_path', models.CharField(help_text='Path to configuration for e.g. puppet, chef.', max_length=100, verbose_name='configuration path')),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('connections', models.ManyToManyField(to='datacenter.DataCenterAsset', through='datacenter.Connection')),
            ],
            options={
                'verbose_name': 'DC Asset',
                'verbose_name_plural': 'DC Assets',
            },
            bases=('assets.asset', models.Model),
        ),
        migrations.CreateModel(
            name='DiskShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('share_id', models.PositiveIntegerField(null=True, verbose_name='share identifier', blank=True)),
                ('label', models.CharField(default=None, max_length=255, null=True, verbose_name='name', blank=True)),
                ('size', models.PositiveIntegerField(null=True, verbose_name='size (MiB)', blank=True)),
                ('snapshot_size', models.PositiveIntegerField(null=True, verbose_name='size for snapshots (MiB)', blank=True)),
                ('wwn', models.CharField(unique=True, max_length=33, verbose_name='Volume serial')),
                ('full', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'disk share',
                'verbose_name_plural': 'disk shares',
            },
        ),
        migrations.CreateModel(
            name='DiskShareMount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('volume', models.CharField(default=None, max_length=255, null=True, verbose_name='volume', blank=True)),
                ('size', models.PositiveIntegerField(null=True, verbose_name='size (MiB)', blank=True)),
            ],
            options={
                'verbose_name': 'disk share mount',
                'verbose_name_plural': 'disk share mounts',
            },
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('description', models.CharField(max_length=250, verbose_name='description', blank=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')])),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(default=0, verbose_name='column number on visualization grid')),
                ('visualization_row', models.PositiveIntegerField(default=0, verbose_name='row number on visualization grid')),
            ],
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(max_length=1024, verbose_name=b'Additional remarks', blank=True)),
                ('accessory', models.ForeignKey(to='datacenter.Accessory')),
                ('rack', models.ForeignKey(to='datacenter.Rack')),
            ],
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('data_center', models.ForeignKey(verbose_name='data center', to='datacenter.DataCenter')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VIP',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
            ],
            options={
                'verbose_name': 'VIP',
                'verbose_name_plural': 'VIPs',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
            ],
            options={
                'verbose_name': 'Virtual server (VM)',
                'verbose_name_plural': 'Virtual servers (VM)',
            },
            bases=('assets.asset',),
        ),
        migrations.AddField(
            model_name='rack',
            name='accessories',
            field=models.ManyToManyField(to='datacenter.Accessory', through='datacenter.RackAccessory'),
        ),
        migrations.AddField(
            model_name='rack',
            name='server_room',
            field=models.ForeignKey(verbose_name='server room', blank=True, to='datacenter.ServerRoom', null=True),
        ),
        migrations.AddField(
            model_name='disksharemount',
            name='asset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.Asset', null=True, verbose_name='asset'),
        ),
        migrations.AddField(
            model_name='disksharemount',
            name='share',
            field=models.ForeignKey(verbose_name='share', to='datacenter.DiskShare'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(related_name='diskshare', to='assets.Asset'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.ComponentModel', null=True, verbose_name='model'),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(to='datacenter.Rack'),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_connections', on_delete=django.db.models.deletion.PROTECT, verbose_name='connected device', to='datacenter.DataCenterAsset'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(related_name='outbound_connections', on_delete=django.db.models.deletion.PROTECT, verbose_name='connected to device', to='datacenter.DataCenterAsset'),
        ),
        migrations.AlterUniqueTogether(
            name='rack',
            unique_together=set([('name', 'server_room')]),
        ),
        migrations.AlterUniqueTogether(
            name='disksharemount',
            unique_together=set([('share', 'asset')]),
        ),
    ]
