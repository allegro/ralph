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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'accessories',
                'verbose_name': 'accessory',
            },
        ),
        migrations.CreateModel(
            name='CloudProject',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.BaseObject', auto_created=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('connection_type', models.PositiveIntegerField(choices=[(1, 'network connection')], verbose_name='connection type')),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.BaseObject', auto_created=True)),
            ],
            options={
                'verbose_name_plural': 'databases',
                'verbose_name': 'database',
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='DataCenter',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('asset_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.Asset', auto_created=True)),
                ('slots', models.FloatField(max_length=64, help_text='For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', default=0, verbose_name='Slots')),
                ('slot_no', models.CharField(null=True, max_length=3, blank=True, help_text='Fill it if asset is blade server', verbose_name='slot number')),
                ('configuration_path', models.CharField(max_length=100, help_text='Path to configuration for e.g. puppet, chef.', verbose_name='configuration path')),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('connections', models.ManyToManyField(through='data_center.Connection', to='data_center.DataCenterAsset')),
            ],
            options={
                'verbose_name_plural': 'data center assets',
                'verbose_name': 'data center asset',
            },
            bases=('assets.asset',),
        ),
        migrations.CreateModel(
            name='DiscoveryQueue',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'discovery queues',
                'ordering': ('name',),
                'verbose_name': 'discovery queue',
            },
        ),
        migrations.CreateModel(
            name='DiskShare',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('share_id', models.PositiveIntegerField(null=True, blank=True, verbose_name='share identifier')),
                ('label', models.CharField(null=True, max_length=255, blank=True, default=None, verbose_name='name')),
                ('size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size (MiB)')),
                ('snapshot_size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size for snapshots (MiB)')),
                ('wwn', models.CharField(unique=True, max_length=33, verbose_name='Volume serial')),
                ('full', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'disk shares',
                'verbose_name': 'disk share',
            },
        ),
        migrations.CreateModel(
            name='DiskShareMount',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('volume', models.CharField(null=True, max_length=255, blank=True, default=None, verbose_name='volume')),
                ('size', models.PositiveIntegerField(null=True, blank=True, verbose_name='size (MiB)')),
                ('asset', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='assets.Asset', verbose_name='asset')),
                ('share', models.ForeignKey(to='data_center.DiskShare', verbose_name='share')),
            ],
            options={
                'verbose_name_plural': 'disk share mounts',
                'verbose_name': 'disk share mount',
            },
        ),
        migrations.CreateModel(
            name='IPAddress',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_seen', models.DateTimeField(auto_now_add=True, verbose_name='last seen')),
                ('address', models.GenericIPAddressField(default=None, null=True, unique=True, blank=True, help_text='Presented as string.', verbose_name='IP address')),
                ('number', models.BigIntegerField(unique=True, editable=False, help_text='Presented as int.', verbose_name='IP address')),
                ('hostname', models.CharField(null=True, max_length=255, blank=True, default=None, verbose_name='hostname')),
                ('is_management', models.BooleanField(default=False, verbose_name='This is a management address')),
                ('is_public', models.BooleanField(editable=False, default=False, verbose_name='This is a public address')),
                ('asset', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='assets.Asset', verbose_name='asset')),
            ],
            options={
                'verbose_name_plural': 'IP addresses',
                'verbose_name': 'IP address',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('address', models.CharField(unique=True, max_length=18, help_text='Presented as string (e.g. 192.168.0.0/24)', validators=[ralph.data_center.models.networks.network_validator], verbose_name='network address')),
                ('gateway', models.GenericIPAddressField(default=None, null=True, blank=True, help_text='Presented as string.', verbose_name='gateway address')),
                ('gateway_as_int', models.PositiveIntegerField(null=True, blank=True, editable=False, default=None, verbose_name='gateway as int')),
                ('reserved', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', default=10, verbose_name='reserved')),
                ('reserved_top_margin', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', default=0, verbose_name='reserved (top margin)')),
                ('remarks', models.TextField(help_text='Additional information.', blank=True, default='', verbose_name='remarks')),
                ('vlan', models.PositiveIntegerField(null=True, blank=True, default=None, verbose_name='VLAN number')),
                ('min_ip', models.PositiveIntegerField(null=True, blank=True, editable=False, default=None, verbose_name='smallest IP number')),
                ('max_ip', models.PositiveIntegerField(null=True, blank=True, editable=False, default=None, verbose_name='largest IP number')),
                ('ignore_addresses', models.BooleanField(help_text='Addresses from this network should never be assigned to any device, because they are not unique.', default=False, verbose_name='Ignore addresses from this network')),
                ('dhcp_broadcast', models.BooleanField(db_index=True, default=False, verbose_name='Broadcast in DHCP configuration')),
                ('dhcp_config', models.TextField(blank=True, default='', verbose_name='DHCP additional configuration')),
                ('data_center', models.ForeignKey(null=True, blank=True, to='data_center.DataCenter', verbose_name='data center')),
            ],
            options={
                'verbose_name_plural': 'networks',
                'ordering': ('vlan',),
                'verbose_name': 'network',
            },
        ),
        migrations.CreateModel(
            name='NetworkEnvironment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('hosts_naming_template', models.CharField(max_length=30, help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', verbose_name='hosts naming template')),
                ('next_server', models.CharField(help_text='The address for a TFTP server for DHCP.', max_length=32, blank=True, default='', verbose_name='next server')),
                ('domain', models.CharField(null=True, max_length=255, blank=True, verbose_name='domain')),
                ('remarks', models.TextField(null=True, blank=True, help_text='Additional information.', verbose_name='remarks')),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', verbose_name='data center')),
                ('queue', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='data_center.DiscoveryQueue', verbose_name='discovery queue')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'network kinds',
                'ordering': ('name',),
                'verbose_name': 'network kind',
            },
        ),
        migrations.CreateModel(
            name='NetworkTerminator',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'network terminators',
                'ordering': ('name',),
                'verbose_name': 'network terminator',
            },
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', verbose_name='data center')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VIP',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.BaseObject', auto_created=True)),
            ],
            options={
                'verbose_name_plural': 'VIPs',
                'verbose_name': 'VIP',
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.BaseObject', auto_created=True)),
            ],
            options={
                'verbose_name_plural': 'Virtual servers (VM)',
                'verbose_name': 'Virtual server (VM)',
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
            field=models.ForeignKey(null=True, blank=True, to='data_center.ServerRoom', verbose_name='server room'),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='data_center.NetworkKind', verbose_name='network kind'),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='data_center.NetworkEnvironment', verbose_name='environment'),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(blank=True, to='data_center.Rack', verbose_name='racks'),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(to='data_center.NetworkTerminator', verbose_name='network terminators'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='network',
            field=models.ForeignKey(default=None, null=True, blank=True, to='data_center.Network', verbose_name='network'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(related_name='diskshare', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='assets.ComponentModel', verbose_name='model'),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(null=True, to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_connections', on_delete=django.db.models.deletion.PROTECT, to='data_center.DataCenterAsset', verbose_name='connected device'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(related_name='outbound_connections', on_delete=django.db.models.deletion.PROTECT, to='data_center.DataCenterAsset', verbose_name='connected to device'),
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
