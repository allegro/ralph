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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('visualization_cols_num', models.PositiveIntegerField(verbose_name='visualization grid columns number', default=20)),
                ('visualization_rows_num', models.PositiveIntegerField(verbose_name='visualization grid rows number', default=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataCenterAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
                ('slots', models.FloatField(verbose_name='Slots', max_length=64, help_text='For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', default=0)),
                ('slot_no', models.CharField(verbose_name='slot number', max_length=3, help_text='Fill it if asset is blade server', null=True, blank=True)),
                ('configuration_path', models.CharField(verbose_name='configuration path', max_length=100, help_text='Path to configuration for e.g. puppet, chef.')),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'discovery queue',
                'verbose_name_plural': 'discovery queues',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='DiskShare',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('share_id', models.PositiveIntegerField(verbose_name='share identifier', blank=True, null=True)),
                ('label', models.CharField(verbose_name='name', max_length=255, blank=True, null=True, default=None)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, null=True)),
                ('snapshot_size', models.PositiveIntegerField(verbose_name='size for snapshots (MiB)', blank=True, null=True)),
                ('wwn', models.CharField(verbose_name='Volume serial', max_length=33, unique=True)),
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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('volume', models.CharField(verbose_name='volume', max_length=255, blank=True, null=True, default=None)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, null=True)),
                ('asset', models.ForeignKey(to='assets.Asset', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='asset', blank=True, default=None)),
                ('share', models.ForeignKey(to='data_center.DiskShare', verbose_name='share')),
            ],
            options={
                'verbose_name': 'disk share mount',
                'verbose_name_plural': 'disk share mounts',
            },
        ),
        migrations.CreateModel(
            name='IPAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_seen', models.DateTimeField(verbose_name='last seen', auto_now_add=True)),
                ('address', models.GenericIPAddressField(help_text='Presented as string.', unique=True, verbose_name='IP address', blank=True, null=True, default=None)),
                ('number', models.BigIntegerField(verbose_name='IP address', help_text='Presented as int.', unique=True, editable=False)),
                ('hostname', models.CharField(verbose_name='hostname', max_length=255, blank=True, null=True, default=None)),
                ('is_management', models.BooleanField(verbose_name='This is a management address', default=False)),
                ('is_public', models.BooleanField(verbose_name='This is a public address', editable=False, default=False)),
                ('asset', models.ForeignKey(to='assets.Asset', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='asset', blank=True, default=None)),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('address', models.CharField(verbose_name='network address', max_length=18, blank=False, validators=[ralph.data_center.models.networks.network_validator], unique=True, help_text='Presented as string (e.g. 192.168.0.0/24)')),
                ('gateway', models.GenericIPAddressField(help_text='Presented as string.', verbose_name='gateway address', blank=True, null=True, default=None)),
                ('gateway_as_int', models.PositiveIntegerField(verbose_name='gateway as int', blank=True, editable=False, null=True, default=None)),
                ('reserved', models.PositiveIntegerField(verbose_name='reserved', help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', default=10)),
                ('reserved_top_margin', models.PositiveIntegerField(verbose_name='reserved (top margin)', help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', default=0)),
                ('remarks', models.TextField(verbose_name='remarks', help_text='Additional information.', blank=True, default='')),
                ('vlan', models.PositiveIntegerField(verbose_name='VLAN number', blank=True, null=True, default=None)),
                ('min_ip', models.PositiveIntegerField(verbose_name='smallest IP number', blank=True, editable=False, null=True, default=None)),
                ('max_ip', models.PositiveIntegerField(verbose_name='largest IP number', blank=True, editable=False, null=True, default=None)),
                ('ignore_addresses', models.BooleanField(verbose_name='Ignore addresses from this network', help_text='Addresses from this network should never be assigned to any device, because they are not unique.', default=False)),
                ('dhcp_broadcast', models.BooleanField(verbose_name='Broadcast in DHCP configuration', db_index=True, default=False)),
                ('dhcp_config', models.TextField(verbose_name='DHCP additional configuration', blank=True, default='')),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', null=True, verbose_name='data center', blank=True)),
            ],
            options={
                'verbose_name': 'network',
                'verbose_name_plural': 'networks',
                'ordering': ('vlan',),
            },
        ),
        migrations.CreateModel(
            name='NetworkEnvironment',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('hosts_naming_template', models.CharField(verbose_name='hosts naming template', max_length=30, help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc')),
                ('next_server', models.CharField(verbose_name='next server', max_length=32, help_text='The address for a TFTP server for DHCP.', blank=True, default='')),
                ('domain', models.CharField(verbose_name='domain', max_length=255, blank=True, null=True)),
                ('remarks', models.TextField(verbose_name='remarks', blank=True, help_text='Additional information.', null=True)),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', verbose_name='data center')),
                ('queue', models.ForeignKey(to='data_center.DiscoveryQueue', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='discovery queue', blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'network kind',
                'verbose_name_plural': 'network kinds',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkTerminator',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'network terminator',
                'verbose_name_plural': 'network terminators',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('description', models.CharField(verbose_name='description', max_length=250, blank=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')], default=1)),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(verbose_name='column number on visualization grid', default=0)),
                ('visualization_row', models.PositiveIntegerField(verbose_name='row number on visualization grid', default=0)),
            ],
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(verbose_name='Additional remarks', max_length=1024, blank=True)),
                ('accessory', models.ForeignKey(to='data_center.Accessory')),
                ('rack', models.ForeignKey(to='data_center.Rack')),
            ],
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', verbose_name='data center')),
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
            field=models.ForeignKey(to='data_center.ServerRoom', null=True, verbose_name='server room', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(to='data_center.NetworkKind', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='network kind', blank=True, default=None),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(to='data_center.NetworkEnvironment', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='environment', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(to='data_center.Rack', verbose_name='racks', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(to='data_center.NetworkTerminator', verbose_name='network terminators'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='network',
            field=models.ForeignKey(to='data_center.Network', null=True, verbose_name='network', blank=True, default=None),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(to='assets.BaseObject', related_name='diskshare'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(to='assets.ComponentModel', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='model', blank=True, default=None),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(to='data_center.Rack', null=True),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(to='data_center.DataCenterAsset', on_delete=django.db.models.deletion.PROTECT, related_name='inbound_connections', verbose_name='connected device'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(to='data_center.DataCenterAsset', on_delete=django.db.models.deletion.PROTECT, related_name='outbound_connections', verbose_name='connected to device'),
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
