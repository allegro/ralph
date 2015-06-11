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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
                ('slots', models.FloatField(default=0, help_text=b'For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', max_length=64, verbose_name=b'Slots')),
                ('slot_no', models.CharField(help_text='Fill it if asset is blade server', max_length=3, null=True, verbose_name='slot number', blank=True)),
                ('configuration_path', models.CharField(help_text='Path to configuration for e.g. puppet, chef.', max_length=100, verbose_name='configuration path')),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('connections', models.ManyToManyField(to='data_center.DataCenterAsset', through='data_center.Connection')),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
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
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.Asset', null=True, verbose_name='asset')),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_seen', models.DateTimeField(auto_now_add=True, verbose_name='last seen')),
                ('address', models.GenericIPAddressField(null=True, default=None, blank=True, help_text='Presented as string.', unique=True, verbose_name='IP address')),
                ('number', models.BigIntegerField(help_text='Presented as int.', verbose_name='IP address', unique=True, editable=False)),
                ('hostname', models.CharField(default=None, max_length=255, null=True, verbose_name='hostname', blank=True)),
                ('is_management', models.BooleanField(default=False, verbose_name='This is a management address')),
                ('is_public', models.BooleanField(default=False, verbose_name='This is a public address', editable=False)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.Asset', null=True, verbose_name='asset')),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('address', models.CharField(help_text='Presented as string (e.g. 192.168.0.0/24)', unique=True, max_length=18, verbose_name='network address', validators=[ralph.data_center.models.networks.network_validator])),
                ('gateway', models.GenericIPAddressField(default=None, blank=True, help_text='Presented as string.', null=True, verbose_name='gateway address')),
                ('gateway_as_int', models.PositiveIntegerField(default=None, verbose_name='gateway as int', null=True, editable=False, blank=True)),
                ('reserved', models.PositiveIntegerField(default=10, help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', verbose_name='reserved')),
                ('reserved_top_margin', models.PositiveIntegerField(default=0, help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', verbose_name='reserved (top margin)')),
                ('remarks', models.TextField(default='', help_text='Additional information.', verbose_name='remarks', blank=True)),
                ('vlan', models.PositiveIntegerField(default=None, null=True, verbose_name='VLAN number', blank=True)),
                ('min_ip', models.PositiveIntegerField(default=None, verbose_name='smallest IP number', null=True, editable=False, blank=True)),
                ('max_ip', models.PositiveIntegerField(default=None, verbose_name='largest IP number', null=True, editable=False, blank=True)),
                ('ignore_addresses', models.BooleanField(default=False, help_text='Addresses from this network should never be assigned to any device, because they are not unique.', verbose_name='Ignore addresses from this network')),
                ('dhcp_broadcast', models.BooleanField(default=False, db_index=True, verbose_name='Broadcast in DHCP configuration')),
                ('dhcp_config', models.TextField(default='', verbose_name='DHCP additional configuration', blank=True)),
                ('data_center', models.ForeignKey(verbose_name='data center', blank=True, to='data_center.DataCenter', null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('hosts_naming_template', models.CharField(help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', max_length=30, verbose_name='hosts naming template')),
                ('next_server', models.CharField(default='', help_text='The address for a TFTP server for DHCP.', max_length=32, verbose_name='next server', blank=True)),
                ('domain', models.CharField(max_length=255, null=True, verbose_name='domain', blank=True)),
                ('remarks', models.TextField(help_text='Additional information.', null=True, verbose_name='remarks', blank=True)),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='discovery queue', blank=True, to='data_center.DiscoveryQueue', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
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
                ('accessory', models.ForeignKey(to='data_center.Accessory')),
                ('rack', models.ForeignKey(to='data_center.Rack')),
            ],
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
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
            field=models.ManyToManyField(to='data_center.Accessory', through='data_center.RackAccessory'),
        ),
        migrations.AddField(
            model_name='rack',
            name='server_room',
            field=models.ForeignKey(verbose_name='server room', blank=True, to='data_center.ServerRoom', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='data_center.NetworkKind', null=True, verbose_name='network kind'),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='environment', blank=True, to='data_center.NetworkEnvironment', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(to='data_center.Rack', null=True, verbose_name='racks', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(to='data_center.NetworkTerminator', verbose_name='network terminators'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='network',
            field=models.ForeignKey(default=None, blank=True, to='data_center.Network', null=True, verbose_name='network'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(related_name='diskshare', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.ComponentModel', null=True, verbose_name='model'),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_connections', on_delete=django.db.models.deletion.PROTECT, verbose_name='connected device', to='data_center.DataCenterAsset'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(related_name='outbound_connections', on_delete=django.db.models.deletion.PROTECT, verbose_name='connected to device', to='data_center.DataCenterAsset'),
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
