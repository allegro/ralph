# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import ralph.lib.transitions.fields
import django.core.validators
import ralph.lib.mixins.fields
import re
import ralph.lib.mixins.models
import ralph.data_center.models.networks


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', serialize=False, parent_link=True, primary_key=True, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('connection_type', models.PositiveIntegerField(verbose_name='connection type', choices=[(1, 'network connection')])),
            ],
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', serialize=False, parent_link=True, primary_key=True, auto_created=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('asset_ptr', models.OneToOneField(to='assets.Asset', serialize=False, parent_link=True, primary_key=True, auto_created=True)),
                ('status', ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in use'), (3, 'free'), (4, 'damaged'), (5, 'liquidated'), (6, 'to deploy')])),
                ('position', models.IntegerField(null=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('slot_no', models.CharField(verbose_name='slot number', help_text='Fill it if asset is blade server', max_length=3, blank=True, null=True, validators=[django.core.validators.RegexValidator(regex=re.compile('^([1-9][A,B]?|1[0-6][A,B]?)$', 32), message="Slot number should be a number from range 1-16 with an optional postfix 'A' or 'B' (e.g. '16A')", code='invalid_slot_no')])),
                ('source', models.PositiveIntegerField(verbose_name='source', null=True, blank=True, db_index=True, choices=[(1, 'shipment'), (2, 'salvaged')])),
                ('delivery_date', models.DateField(null=True, blank=True)),
                ('production_year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('production_use_date', models.DateField(null=True, blank=True)),
                ('management_ip', models.GenericIPAddressField(verbose_name='Management IP address', help_text='Presented as string.', default=None, null=True, unique=True, blank=True)),
                ('management_hostname', ralph.lib.mixins.fields.NullableCharField(max_length=100, null=True, unique=True, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('share_id', models.PositiveIntegerField(verbose_name='share identifier', null=True, blank=True)),
                ('label', models.CharField(max_length=255, verbose_name='name', null=True, blank=True, default=None)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', null=True, blank=True)),
                ('snapshot_size', models.PositiveIntegerField(verbose_name='size for snapshots (MiB)', null=True, blank=True)),
                ('wwn', ralph.lib.mixins.fields.NullableCharField(max_length=33, verbose_name='Volume serial', unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('volume', models.CharField(max_length=255, verbose_name='volume', null=True, blank=True, default=None)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', null=True, blank=True)),
                ('asset', models.ForeignKey(verbose_name='asset', default=None, to='assets.Asset', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_seen', models.DateTimeField(verbose_name='last seen', auto_now_add=True)),
                ('address', models.GenericIPAddressField(verbose_name='IP address', help_text='Presented as string.', default=None, null=True, unique=True)),
                ('hostname', models.CharField(max_length=255, verbose_name='Hostname', null=True, blank=True, default=None)),
                ('number', models.BigIntegerField(verbose_name='IP address', help_text='Presented as int.', editable=False, unique=True)),
                ('is_management', models.BooleanField(verbose_name='This is a management address', default=False)),
                ('is_public', models.BooleanField(verbose_name='This is a public address', default=False, editable=False)),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('address', models.CharField(max_length=18, help_text='Presented as string (e.g. 192.168.0.0/24)', verbose_name='network address', validators=[ralph.data_center.models.networks.network_validator], unique=True)),
                ('gateway', models.GenericIPAddressField(verbose_name='gateway address', help_text='Presented as string.', default=None, null=True, blank=True)),
                ('gateway_as_int', models.BigIntegerField(verbose_name='gateway as int', default=None, editable=False, blank=True, null=True)),
                ('reserved', models.PositiveIntegerField(verbose_name='reserved', help_text='Number of addresses to be omitted in the automatic determination process, counted from the first in range.', default=10)),
                ('reserved_top_margin', models.PositiveIntegerField(verbose_name='reserved (top margin)', help_text='Number of addresses to be omitted in the automatic determination process, counted from the last in range.', default=0)),
                ('remarks', models.TextField(verbose_name='remarks', help_text='Additional information.', blank=True, default='')),
                ('vlan', models.PositiveIntegerField(verbose_name='VLAN number', default=None, null=True, blank=True)),
                ('min_ip', models.BigIntegerField(verbose_name='smallest IP number', default=None, editable=False, blank=True, null=True)),
                ('max_ip', models.BigIntegerField(verbose_name='largest IP number', default=None, editable=False, blank=True, null=True)),
                ('ignore_addresses', models.BooleanField(verbose_name='Ignore addresses from this network', help_text='Addresses from this network should never be assigned to any device, because they are not unique.', default=False)),
                ('dhcp_broadcast', models.BooleanField(verbose_name='Broadcast in DHCP configuration', default=False, db_index=True)),
                ('dhcp_config', models.TextField(verbose_name='DHCP additional configuration', default='', blank=True)),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter', null=True, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('hosts_naming_template', models.CharField(max_length=30, help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', verbose_name='hosts naming template')),
                ('next_server', models.CharField(max_length=32, help_text='The address for a TFTP server for DHCP.', verbose_name='next server', blank=True, default='')),
                ('domain', models.CharField(max_length=255, verbose_name='domain', null=True, blank=True)),
                ('remarks', models.TextField(verbose_name='remarks', help_text='Additional information.', null=True, blank=True)),
                ('data_center', models.ForeignKey(verbose_name='data center', to='data_center.DataCenter')),
                ('queue', models.ForeignKey(verbose_name='discovery queue', to='data_center.DiscoveryQueue', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='NetworkKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('description', models.CharField(max_length=250, verbose_name='description', blank=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'top'), (2, 'bottom'), (3, 'left'), (4, 'right')])),
                ('max_u_height', models.IntegerField(default=48)),
                ('visualization_col', models.PositiveIntegerField(verbose_name='column number on visualization grid', default=0)),
                ('visualization_row', models.PositiveIntegerField(verbose_name='row number on visualization grid', default=0)),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RackAccessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('orientation', models.PositiveIntegerField(default=1, choices=[(1, 'front'), (2, 'back'), (3, 'middle'), (101, 'left'), (102, 'right')])),
                ('position', models.IntegerField(null=True)),
                ('remarks', models.CharField(max_length=1024, verbose_name='Additional remarks', blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', serialize=False, parent_link=True, primary_key=True, auto_created=True)),
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
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', serialize=False, parent_link=True, primary_key=True, auto_created=True)),
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
            field=models.ForeignKey(verbose_name='server room', to='data_center.ServerRoom', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(verbose_name='network kind', default=None, to='data_center.NetworkKind', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(verbose_name='environment', to='data_center.NetworkEnvironment', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='racks',
            field=models.ManyToManyField(verbose_name='racks', to='data_center.Rack', blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(verbose_name='network terminators', to='data_center.NetworkTerminator'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='base_object',
            field=models.ForeignKey(verbose_name='Base object', default=None, to='assets.BaseObject', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='asset',
            field=models.ForeignKey(to='assets.BaseObject', related_name='diskshare'),
        ),
        migrations.AddField(
            model_name='diskshare',
            name='model',
            field=models.ForeignKey(verbose_name='model', default=None, to='assets.ComponentModel', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='rack',
            field=models.ForeignKey(to='data_center.Rack', null=True),
        ),
        migrations.AddField(
            model_name='connection',
            name='inbound',
            field=models.ForeignKey(verbose_name='connected device', to='data_center.DataCenterAsset', on_delete=django.db.models.deletion.PROTECT, related_name='inbound_connections'),
        ),
        migrations.AddField(
            model_name='connection',
            name='outbound',
            field=models.ForeignKey(verbose_name='connected to device', to='data_center.DataCenterAsset', on_delete=django.db.models.deletion.PROTECT, related_name='outbound_connections'),
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
