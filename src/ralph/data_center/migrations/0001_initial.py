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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'verbose_name': 'accessory',
                'verbose_name_plural': 'accessories',
            },
        ),
        migrations.CreateModel(
            name='CloudProject',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('connection_type', models.PositiveIntegerField(verbose_name='connection type', choices=[(1, 'network connection')])),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True, auto_created=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
                ('asset_ptr', models.OneToOneField(serialize=False, to='assets.Asset', primary_key=True, parent_link=True, auto_created=True)),
                ('slots', models.FloatField(verbose_name='Slots', default=0, help_text='For blade centers: the number of slots available in this device. For blade devices: the number of slots occupied.', max_length=64)),
                ('slot_no', models.CharField(verbose_name='slot number', null=True, blank=True, help_text='Fill it if asset is blade server', max_length=3)),
                ('configuration_path', models.CharField(verbose_name='configuration path', help_text='Path to configuration for e.g. puppet, chef.', max_length=100)),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('share_id', models.PositiveIntegerField(verbose_name='share identifier', blank=True, null=True)),
                ('label', models.CharField(verbose_name='name', default=None, null=True, blank=True, max_length=255)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, null=True)),
                ('snapshot_size', models.PositiveIntegerField(verbose_name='size for snapshots (MiB)', blank=True, null=True)),
                ('wwn', models.CharField(verbose_name='Volume serial', unique=True, max_length=33)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('volume', models.CharField(verbose_name='volume', default=None, null=True, blank=True, max_length=255)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, null=True)),
                ('asset', models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='asset', to='assets.Asset', null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_seen', models.DateTimeField(verbose_name='last seen', auto_now_add=True)),
                ('address', models.GenericIPAddressField(default=None, unique=True, blank=True, verbose_name='IP address', help_text='Presented as string.', null=True)),
                ('number', models.BigIntegerField(verbose_name='IP address', editable=False, unique=True, help_text='Presented as int.')),
                ('hostname', models.CharField(verbose_name='hostname', default=None, null=True, blank=True, max_length=255)),
                ('is_management', models.BooleanField(verbose_name='This is a management address', default=False)),
                ('is_public', models.BooleanField(verbose_name='This is a public address', default=False, editable=False)),
                ('asset', models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='asset', to='assets.Asset', null=True)),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('address', models.CharField(verbose_name='network address', unique=True, validators=[ralph.data_center.models.networks.network_validator], help_text='Presented as string (e.g. 192.168.0.0/24)', max_length=18)),
                ('gateway', models.GenericIPAddressField(default=None, blank=True, verbose_name='gateway address', help_text='Presented as string.', null=True)),
                ('gateway_as_int', models.PositiveIntegerField(verbose_name='gateway as int', default=None, null=True, blank=True, editable=False)),
                ('reserved', models.PositiveIntegerField(verbose_name='reserved', default=10, help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.')),
                ('reserved_top_margin', models.PositiveIntegerField(verbose_name='reserved (top margin)', default=0, help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.')),
                ('remarks', models.TextField(verbose_name='remarks', default='', blank=True, help_text='Additional information.')),
                ('vlan', models.PositiveIntegerField(verbose_name='VLAN number', default=None, blank=True, null=True)),
                ('min_ip', models.PositiveIntegerField(verbose_name='smallest IP number', default=None, null=True, blank=True, editable=False)),
                ('max_ip', models.PositiveIntegerField(verbose_name='largest IP number', default=None, null=True, blank=True, editable=False)),
                ('ignore_addresses', models.BooleanField(verbose_name='Ignore addresses from this network', default=False, help_text='Addresses from this network should never be assigned to any device, because they are not unique.')),
                ('dhcp_broadcast', models.BooleanField(verbose_name='Broadcast in DHCP configuration', default=False, db_index=True)),
                ('dhcp_config', models.TextField(verbose_name='DHCP additional configuration', default='', blank=True)),
                ('data_center', models.ForeignKey(blank=True, verbose_name='data center', to='data_center.DataCenter', null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('hosts_naming_template', models.CharField(verbose_name='hosts naming template', help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', max_length=30)),
                ('next_server', models.CharField(verbose_name='next server', default='', blank=True, help_text='The address for a TFTP server for DHCP.', max_length=32)),
                ('domain', models.CharField(verbose_name='domain', null=True, blank=True, max_length=255)),
                ('remarks', models.TextField(verbose_name='remarks', blank=True, help_text='Additional information.', null=True)),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='discovery queue', to='data_center.DiscoveryQueue', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('description', models.CharField(verbose_name='description', blank=True, max_length=250)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')])),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(verbose_name='column number on visualization grid', default=0)),
                ('visualization_row', models.PositiveIntegerField(verbose_name='row number on visualization grid', default=0)),
            ],
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(verbose_name='Additional remarks', blank=True, max_length=1024)),
                ('accessory', models.ForeignKey(to='data_center.Accessory')),
                ('rack', models.ForeignKey(to='data_center.Rack')),
            ],
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VIP',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True, auto_created=True)),
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
                ('baseobject_ptr', models.OneToOneField(serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True, auto_created=True)),
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
            field=models.ForeignKey(blank=True, verbose_name='server room', to='data_center.ServerRoom', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='network kind', to='data_center.NetworkKind', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='environment', to='data_center.NetworkEnvironment', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(verbose_name='racks', blank=True, to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(verbose_name='network terminators', to='data_center.NetworkTerminator'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='network',
            field=models.ForeignKey(default=None, blank=True, verbose_name='network', to='data_center.Network', null=True),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(related_name='diskshare', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='model', to='assets.ComponentModel', null=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(to='data_center.Rack', null=True),
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
