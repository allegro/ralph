# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.db.models.deletion
import ralph.assets.models.networks


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetLastHostname',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('prefix', models.CharField(max_length=8, db_index=True)),
                ('counter', models.PositiveIntegerField(default=1)),
                ('postfix', models.CharField(max_length=8, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('type', models.PositiveIntegerField(verbose_name='type', choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')])),
                ('power_consumption', models.IntegerField(default=0, verbose_name='Power consumption', blank=True)),
                ('height_of_device', models.FloatField(default=0, verbose_name='Height of device', blank=True)),
                ('cores_count', models.IntegerField(default=0, verbose_name='Cores count', blank=True)),
                ('visualization_layout_front', models.PositiveIntegerField(default=1, blank=True, verbose_name='visualization layout of front side', choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')])),
                ('visualization_layout_back', models.PositiveIntegerField(default=1, blank=True, verbose_name='visualization layout of back side', choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')])),
            ],
            options={
                'verbose_name': 'model',
                'verbose_name_plural': 'models',
            },
        ),
        migrations.CreateModel(
            name='BaseObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('remarks', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('code', models.CharField(default='', max_length=4, blank=True)),
                ('is_blade', models.BooleanField()),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='ComponentModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('speed', models.PositiveIntegerField(default=0, verbose_name='speed (MHz)', blank=True)),
                ('cores', models.PositiveIntegerField(default=0, verbose_name='number of cores', blank=True)),
                ('size', models.PositiveIntegerField(default=0, verbose_name='size (MiB)', blank=True)),
                ('type', models.PositiveIntegerField(default=8, verbose_name='component type', choices=[(1, 'processor'), (2, 'memory'), (3, 'disk drive'), (4, 'ethernet card'), (5, 'expansion card'), (6, 'fibre channel card'), (7, 'disk share'), (8, 'unknown'), (9, 'management'), (10, 'power module'), (11, 'cooling device'), (12, 'media tray'), (13, 'chassis'), (14, 'backup'), (15, 'software'), (16, 'operating system')])),
                ('family', models.CharField(default=b'', max_length=128, blank=True)),
            ],
            options={
                'verbose_name': 'component model',
                'verbose_name_plural': 'component models',
            },
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
            name='Environment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenericComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(default=None, max_length=255, null=True, verbose_name='label', blank=True)),
                ('sn', models.CharField(null=True, default=None, max_length=255, blank=True, unique=True, verbose_name='vendor SN')),
            ],
            options={
                'verbose_name': 'generic component',
                'verbose_name_plural': 'generic components',
            },
        ),
        migrations.CreateModel(
            name='IPAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_seen', models.DateTimeField(default=datetime.datetime.now, verbose_name='last seen')),
                ('address', models.GenericIPAddressField(null=True, default=None, blank=True, help_text='Presented as string.', unique=True, verbose_name='IP address')),
                ('number', models.BigIntegerField(help_text='Presented as int.', verbose_name='IP address', unique=True, editable=False)),
                ('hostname', models.CharField(default=None, max_length=255, null=True, verbose_name='hostname', blank=True)),
                ('snmp_name', models.TextField(default=None, null=True, verbose_name='name from SNMP', blank=True)),
                ('snmp_community', models.CharField(default=None, max_length=64, null=True, verbose_name='SNMP community', blank=True)),
                ('snmp_version', models.CharField(default=None, max_length=5, null=True, verbose_name='SNMP version', blank=True)),
                ('http_family', models.TextField(default=None, max_length=64, null=True, verbose_name='family from HTTP', blank=True)),
                ('is_management', models.BooleanField(default=False, verbose_name='This is a management address')),
                ('dns_info', models.TextField(default=None, null=True, verbose_name='information from DNS TXT fields', blank=True)),
                ('last_plugins', models.TextField(verbose_name='last plugins', blank=True)),
                ('dead_ping_count', models.IntegerField(default=0, verbose_name='dead ping count')),
                ('is_buried', models.BooleanField(default=False, verbose_name='Buried from autoscan')),
                ('is_public', models.BooleanField(default=False, verbose_name='This is a public address', editable=False)),
            ],
            options={
                'verbose_name': 'IP address',
                'verbose_name_plural': 'IP addresses',
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('address', models.CharField(help_text='Presented as string (e.g. 192.168.0.0/24)', unique=True, max_length=18, verbose_name='network address', validators=[ralph.assets.models.networks.network_validator])),
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
                ('last_scan', models.DateTimeField(default=None, verbose_name='last scan', null=True, editable=False, blank=True)),
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
                ('hosts_naming_template', models.CharField(help_text='E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc', max_length=30)),
                ('next_server', models.CharField(default='', help_text='The address for a TFTP server for DHCP.', max_length=32, blank=True)),
                ('domain', models.CharField(max_length=255, null=True, verbose_name='domain', blank=True)),
                ('remarks', models.TextField(help_text='Additional information.', null=True, verbose_name='remarks', blank=True)),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='discovery queue', blank=True, to='assets.DiscoveryQueue', null=True)),
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
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('profit_center', models.CharField(max_length=100, blank=True)),
                ('cost_center', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('environment', models.ForeignKey(to='assets.Environment')),
                ('service', models.ForeignKey(to='assets.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.BaseObject')),
                ('hostname', models.CharField(default=None, max_length=16, null=True, blank=True)),
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
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.AddField(
            model_name='service',
            name='environments',
            field=models.ManyToManyField(to='assets.Environment', through='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.NetworkKind', null=True, verbose_name='network kind'),
        ),
        migrations.AddField(
            model_name='network',
            name='network_environment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='environment', blank=True, to='assets.NetworkEnvironment', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(to='assets.NetworkTerminator', verbose_name='network terminators'),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='network',
            field=models.ForeignKey(default=None, blank=True, to='assets.Network', null=True, verbose_name='network'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='asset',
            field=models.ForeignKey(related_name='genericcomponent', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.ComponentModel', null=True, verbose_name='model'),
        ),
        migrations.AlterUniqueTogether(
            name='componentmodel',
            unique_together=set([('speed', 'cores', 'size', 'type', 'family')]),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='service_env',
            field=models.ForeignKey(to='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='category',
            field=models.ForeignKey(related_name='models', to='assets.Category', null=True),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='assets.Manufacturer', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='assetlasthostname',
            unique_together=set([('prefix', 'postfix')]),
        ),
        migrations.AddField(
            model_name='ipaddress',
            name='asset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='assets.Asset', null=True, verbose_name='asset'),
        ),
        migrations.AddField(
            model_name='asset',
            name='model',
            field=models.ForeignKey(to='assets.AssetModel'),
        ),
    ]
