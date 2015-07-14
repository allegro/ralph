# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import ralph.data_center.models.networks


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'verbose_name': 'accessory',
                'verbose_name_plural': 'accessories',
            },
        ),
        migrations.CreateModel(
            name='CloudProject',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.BaseObject', serialize=False, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('connection_type', models.PositiveIntegerField(choices=[(1, 'network connection')], verbose_name='connection type')),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.BaseObject', serialize=False, auto_created=True)),
            ],
            options={
                'verbose_name': 'database',
                'verbose_name_plural': 'databases',
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='DataCenter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('asset_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.Asset', serialize=False, auto_created=True)),
                ('slots', models.FloatField(help_text='For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', max_length=64, default=0, verbose_name='Slots')),
                ('slot_no', models.CharField(help_text='Fill it if asset is blade server', max_length=3, blank=True, verbose_name='slot number', null=True)),
                ('configuration_path', models.CharField(help_text='Path to configuration for e.g. puppet, chef.', max_length=100, verbose_name='configuration path')),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('connections', models.ManyToManyField(through='data_center.Connection', to='data_center.DataCenterAsset')),
            ],
            options={
                'verbose_name': 'data center asset',
                'verbose_name_plural': 'data center assets',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='DiscoveryQueue',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'discovery queue',
                'verbose_name_plural': 'discovery queues',
            },
        ),
        migrations.CreateModel(
            name='DiskShare',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('share_id', models.PositiveIntegerField(null=True, blank=True, verbose_name='share identifier')),
                ('label', models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name='name')),
                ('size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size (MiB)')),
                ('snapshot_size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size for snapshots (MiB)')),
                ('wwn', models.CharField(max_length=33, verbose_name='Volume serial', unique=True)),
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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('volume', models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name='volume')),
                ('size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size (MiB)')),
                ('asset', models.ForeignKey(blank=True, to='assets.Asset', null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='asset')),
                ('share', models.ForeignKey(verbose_name='share', to='data_center.DiskShare')),
            ],
            options={
                'verbose_name': 'disk share mount',
                'verbose_name_plural': 'disk share mounts',
            },
        ),
        migrations.CreateModel(
            name='IPAddress',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_seen', models.DateTimeField(verbose_name='last seen', auto_now_add=True)),
                ('address', models.GenericIPAddressField(default=None, unique=True, help_text='Presented as string.', null=True, verbose_name='IP address')),
                ('number', models.BigIntegerField(help_text='Presented as int.', verbose_name='IP address', unique=True, editable=False)),
                ('hostname', models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name='hostname')),
                ('is_management', models.BooleanField(default=False, verbose_name='This is a management address')),
                ('is_public', models.BooleanField(verbose_name='This is a public address', default=False, editable=False)),
                ('asset', models.ForeignKey(blank=True, to='assets.Asset', null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='asset')),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('address', models.CharField(help_text='Presented as string (e.g. 192.168.0.0/24)', max_length=18, validators=[ralph.data_center.models.networks.network_validator], verbose_name='network address', unique=True)),
                ('gateway', models.GenericIPAddressField(blank=True, help_text='Presented as string.', null=True, default=None, verbose_name='gateway address')),
                ('gateway_as_int', models.PositiveIntegerField(verbose_name='gateway as int', null=True, blank=True, default=None, editable=False)),
                ('reserved', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', default=10, verbose_name='reserved')),
                ('reserved_top_margin', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', default=0, verbose_name='reserved (top margin)')),
                ('remarks', models.TextField(help_text='Additional information.', blank=True, default='', verbose_name='remarks')),
                ('vlan', models.PositiveIntegerField(null=True, blank=True, default=None, verbose_name='VLAN number')),
                ('min_ip', models.PositiveIntegerField(verbose_name='smallest IP number', null=True, blank=True, default=None, editable=False)),
                ('max_ip', models.PositiveIntegerField(verbose_name='largest IP number', null=True, blank=True, default=None, editable=False)),
                ('ignore_addresses', models.BooleanField(help_text='Addresses from this network should never be assigned to any device, because they are not unique.', default=False, verbose_name='Ignore addresses from this network')),
                ('dhcp_broadcast', models.BooleanField(db_index=True, default=False, verbose_name='Broadcast in DHCP configuration')),
                ('dhcp_config', models.TextField(blank=True, default='', verbose_name='DHCP additional configuration')),
                ('data_center', models.ForeignKey(blank=True, to='data_center.DataCenter', null=True, verbose_name='data center')),
            ],
            options={
                'ordering': ('vlan',),
                'verbose_name': 'network',
                'verbose_name_plural': 'networks',
            },
        ),
        migrations.CreateModel(
            name='NetworkEnvironment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('hosts_naming_template', models.CharField(help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', max_length=30, verbose_name='hosts naming template')),
                ('next_server', models.CharField(help_text='The address for a TFTP server for DHCP.', max_length=32, blank=True, default='', verbose_name='next server')),
                ('domain', models.CharField(max_length=255, null=True, blank=True, verbose_name='domain')),
                ('remarks', models.TextField(help_text='Additional information.', null=True, blank=True, verbose_name='remarks')),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
                ('queue', models.ForeignKey(blank=True, to='data_center.DiscoveryQueue', null=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='discovery queue')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'network kind',
                'verbose_name_plural': 'network kinds',
            },
        ),
        migrations.CreateModel(
            name='NetworkTerminator',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'network terminator',
                'verbose_name_plural': 'network terminators',
            },
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('description', models.CharField(max_length=250, blank=True, verbose_name='description')),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')], default=1)),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(default=0, verbose_name='column number on visualization grid')),
                ('visualization_row', models.PositiveIntegerField(default=0, verbose_name='row number on visualization grid')),
            ],
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(max_length=1024, blank=True, verbose_name='Additional remarks')),
                ('accessory', models.ForeignKey(to='data_center.Accessory')),
                ('rack', models.ForeignKey(to='data_center.Rack')),
            ],
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VIP',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.BaseObject', serialize=False, auto_created=True)),
            ],
            options={
                'verbose_name': 'VIP',
                'verbose_name_plural': 'VIPs',
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='assets.BaseObject', serialize=False, auto_created=True)),
            ],
            options={
                'verbose_name': 'Virtual server (VM)',
                'verbose_name_plural': 'Virtual servers (VM)',
            },
            bases=('assets.baseobject',),
        ),
        migrations.AddField(
            model_name='rack',
            name='accessories',
            field=models.ManyToManyField(through='data_center.RackAccessory', to='data_center.Accessory'),
        ),
        migrations.AddField(
            model_name='rack',
            name='server_room',
            field=models.ForeignKey(blank=True, to='data_center.ServerRoom', null=True, verbose_name='server room'),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(blank=True, to='data_center.NetworkKind', null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='network kind'),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(blank=True, to='data_center.NetworkEnvironment', null=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='environment'),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(blank=True, verbose_name='racks', to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(verbose_name='network terminators', to='data_center.NetworkTerminator'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(related_name='diskshare', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(blank=True, to='assets.ComponentModel', null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, verbose_name='model'),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(null=True, to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(verbose_name='connected device', on_delete=django.db.models.deletion.PROTECT, to='data_center.DataCenterAsset', related_name='inbound_connections'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(verbose_name='connected to device', on_delete=django.db.models.deletion.PROTECT, to='data_center.DataCenterAsset', related_name='outbound_connections'),
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
