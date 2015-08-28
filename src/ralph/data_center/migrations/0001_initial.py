# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.fields
import re
import ralph.data_center.models.networks
import ralph.lib.mixins.models
import ralph.lib.transitions.fields
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('connection_type', models.PositiveIntegerField(choices=[(1, 'network connection')], verbose_name='connection type')),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('asset_ptr', models.OneToOneField(to='assets.Asset', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
                ('status', ralph.lib.transitions.fields.TransitionField(choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')], default=1)),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('slot_no', models.CharField(null=True, verbose_name='slot number', validators=[django.core.validators.RegexValidator(regex=re.compile('^([1-9][A,B]?|1[0-6][A,B]?)$', 32), code='invalid_slot_no', message="Slot number should be a number from range 1-16 with an optional postfix 'A' or 'B' (e.g. '16A')")], help_text='Fill it if asset is blade server', blank=True, max_length=3)),
                ('configuration_path', models.CharField(help_text='Path to configuration for e.g. puppet, chef.', verbose_name='configuration path', max_length=100)),
                ('source', models.PositiveIntegerField(null=True, choices=[(1, 'shipment'), (2, 'salvaged')], verbose_name='source', db_index=True, blank=True)),
                ('delivery_date', models.DateField(null=True, blank=True)),
                ('production_year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('production_use_date', models.DateField(null=True, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('share_id', models.PositiveIntegerField(null=True, verbose_name='share identifier', blank=True)),
                ('label', models.CharField(null=True, verbose_name='name', blank=True, default=None, max_length=255)),
                ('size', models.PositiveIntegerField(null=True, verbose_name='size (MiB)', blank=True)),
                ('snapshot_size', models.PositiveIntegerField(null=True, verbose_name='size for snapshots (MiB)', blank=True)),
                ('wwn', ralph.lib.mixins.fields.NullableCharField(verbose_name='Volume serial', max_length=33, unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('volume', models.CharField(null=True, verbose_name='volume', blank=True, default=None, max_length=255)),
                ('size', models.PositiveIntegerField(null=True, verbose_name='size (MiB)', blank=True)),
                ('asset', models.ForeignKey(null=True, to='assets.Asset', verbose_name='asset', default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_seen', models.DateTimeField(verbose_name='last seen', auto_now_add=True)),
                ('address', models.GenericIPAddressField(null=True, verbose_name='IP address', default=None, unique=True, help_text='Presented as string.')),
                ('number', models.BigIntegerField(editable=False, verbose_name='IP address', help_text='Presented as int.', unique=True)),
                ('is_management', models.BooleanField(verbose_name='This is a management address', default=False)),
                ('is_public', models.BooleanField(editable=False, verbose_name='This is a public address', default=False)),
                ('asset', models.ForeignKey(null=True, to='assets.Asset', verbose_name='asset', default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True)),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('address', models.CharField(help_text='Presented as string (e.g. 192.168.0.0/24)', verbose_name='network address', max_length=18, validators=[ralph.data_center.models.networks.network_validator], unique=True)),
                ('gateway', models.GenericIPAddressField(null=True, verbose_name='gateway address', default=None, help_text='Presented as string.', blank=True)),
                ('gateway_as_int', models.PositiveIntegerField(null=True, editable=False, verbose_name='gateway as int', blank=True, default=None)),
                ('reserved', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', verbose_name='reserved', default=10)),
                ('reserved_top_margin', models.PositiveIntegerField(help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', verbose_name='reserved (top margin)', default=0)),
                ('remarks', models.TextField(help_text='Additional information.', verbose_name='remarks', blank=True, default='')),
                ('vlan', models.PositiveIntegerField(null=True, verbose_name='VLAN number', blank=True, default=None)),
                ('min_ip', models.PositiveIntegerField(null=True, editable=False, verbose_name='smallest IP number', blank=True, default=None)),
                ('max_ip', models.PositiveIntegerField(null=True, editable=False, verbose_name='largest IP number', blank=True, default=None)),
                ('ignore_addresses', models.BooleanField(help_text='Addresses from this network should never be assigned to any device, because they are not unique.', verbose_name='Ignore addresses from this network', default=False)),
                ('dhcp_broadcast', models.BooleanField(verbose_name='Broadcast in DHCP configuration', db_index=True, default=False)),
                ('dhcp_config', models.TextField(verbose_name='DHCP additional configuration', blank=True, default='')),
                ('data_center', models.ForeignKey(null=True, to='data_center.DataCenter', verbose_name='data center', blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('hosts_naming_template', models.CharField(help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', verbose_name='hosts naming template', max_length=30)),
                ('next_server', models.CharField(help_text='The address for a TFTP server for DHCP.', verbose_name='next server', blank=True, default='', max_length=32)),
                ('domain', models.CharField(null=True, verbose_name='domain', blank=True, max_length=255)),
                ('remarks', models.TextField(null=True, help_text='Additional information.', verbose_name='remarks', blank=True)),
                ('data_center', models.ForeignKey(to='data_center.DataCenter', verbose_name='data center')),
                ('queue', models.ForeignKey(null=True, to='data_center.DiscoveryQueue', verbose_name='discovery queue', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('description', models.CharField(verbose_name='description', blank=True, max_length=250)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')], default=1)),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(verbose_name='column number on visualization grid', default=0)),
                ('visualization_row', models.PositiveIntegerField(verbose_name='row number on visualization grid', default=0)),
            ],
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('orientation', models.PositiveIntegerField(choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')], default=1)),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(verbose_name='Additional remarks', blank=True, max_length=1024)),
                ('accessory', models.ForeignKey(to='data_center.Accessory')),
                ('rack', models.ForeignKey(to='data_center.Rack')),
            ],
            options={
                'verbose_name_plural': 'rack accessories',
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ServerRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
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
            field=models.ForeignKey(null=True, to='data_center.ServerRoom', verbose_name='server room', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(null=True, to='data_center.NetworkKind', verbose_name='network kind', default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(null=True, to='data_center.NetworkEnvironment', verbose_name='environment', on_delete=django.db.models.deletion.SET_NULL, blank=True),
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
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(to='assets.BaseObject', related_name='diskshare'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(null=True, to='assets.ComponentModel', verbose_name='model', default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(null=True, to='data_center.Rack'),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(to='data_center.DataCenterAsset', verbose_name='connected device', on_delete=django.db.models.deletion.PROTECT, related_name='inbound_connections'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(to='data_center.DataCenterAsset', verbose_name='connected to device', on_delete=django.db.models.deletion.PROTECT, related_name='outbound_connections'),
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
