# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetLastHostname',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('prefix', models.CharField(db_index=True, max_length=8)),
                ('counter', models.PositiveIntegerField(default=1)),
                ('postfix', models.CharField(db_index=True, max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='AssetModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('type', models.PositiveIntegerField(verbose_name='type', choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')])),
                ('power_consumption', models.IntegerField(verbose_name='Power consumption', default=0, blank=True)),
                ('height_of_device', models.FloatField(verbose_name='Height of device', default=0, blank=True)),
                ('cores_count', models.IntegerField(verbose_name='Cores count', default=0, blank=True)),
                ('visualization_layout_front', models.PositiveIntegerField(verbose_name='visualization layout of front side', default=1, blank=True, choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')])),
                ('visualization_layout_back', models.PositiveIntegerField(verbose_name='visualization layout of back side', default=1, blank=True, choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')])),
                ('has_parent', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'model',
                'verbose_name_plural': 'models',
            },
        ),
        migrations.CreateModel(
            name='BaseObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('remarks', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('code', models.CharField(default='', blank=True, max_length=4)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='assets.Category', null=True)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='ComponentModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('speed', models.PositiveIntegerField(verbose_name='speed (MHz)', default=0, blank=True)),
                ('cores', models.PositiveIntegerField(verbose_name='number of cores', default=0, blank=True)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', default=0, blank=True)),
                ('type', models.PositiveIntegerField(verbose_name='component type', default=8, choices=[(1, 'processor'), (2, 'memory'), (3, 'disk drive'), (4, 'ethernet card'), (5, 'expansion card'), (6, 'fibre channel card'), (7, 'disk share'), (8, 'unknown'), (9, 'management'), (10, 'power module'), (11, 'cooling device'), (12, 'media tray'), (13, 'chassis'), (14, 'backup'), (15, 'software'), (16, 'operating system')])),
                ('family', models.CharField(default='', blank=True, max_length=128)),
            ],
            options={
                'verbose_name': 'component model',
                'verbose_name_plural': 'component models',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenericComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('label', models.CharField(verbose_name='label', default=None, null=True, blank=True, max_length=255)),
                ('sn', models.CharField(default=None, unique=True, blank=True, max_length=255, verbose_name='vendor SN', null=True)),
            ],
            options={
                'verbose_name': 'generic component',
                'verbose_name_plural': 'generic components',
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('profit_center', models.CharField(blank=True, max_length=100)),
                ('cost_center', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('environment', models.ForeignKey(to='assets.Environment')),
                ('service', models.ForeignKey(to='assets.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('baseobject_ptr', models.OneToOneField(serialize=False, to='assets.BaseObject', primary_key=True, parent_link=True, auto_created=True)),
                ('hostname', models.CharField(default=None, null=True, blank=True, max_length=255)),
                ('niw', models.CharField(verbose_name='Inventory number', default=None, null=True, blank=True, max_length=200)),
                ('invoice_no', models.CharField(null=True, db_index=True, blank=True, max_length=128)),
                ('required_support', models.BooleanField(default=False)),
                ('order_no', models.CharField(null=True, blank=True, max_length=50)),
                ('purchase_order', models.CharField(null=True, blank=True, max_length=50)),
                ('invoice_date', models.DateField(blank=True, null=True)),
                ('sn', models.CharField(null=True, unique=True, blank=True, max_length=200)),
                ('barcode', models.CharField(default=None, null=True, unique=True, blank=True, max_length=200)),
                ('price', models.DecimalField(default=0, max_digits=10, decimal_places=2, blank=True, null=True)),
                ('provider', models.CharField(null=True, blank=True, max_length=100)),
                ('source', models.PositiveIntegerField(verbose_name='source', db_index=True, blank=True, choices=[(1, 'shipment'), (2, 'salvaged')], null=True)),
                ('status', models.PositiveSmallIntegerField(verbose_name='status', default=1, blank=True, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')], null=True)),
                ('request_date', models.DateField(blank=True, null=True)),
                ('delivery_date', models.DateField(blank=True, null=True)),
                ('production_use_date', models.DateField(blank=True, null=True)),
                ('provider_order_date', models.DateField(blank=True, null=True)),
                ('deprecation_rate', models.DecimalField(default=25, max_digits=5, decimal_places=2, blank=True, help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .')),
                ('force_deprecation', models.BooleanField(help_text='Check if you no longer want to bill for this asset')),
                ('deprecation_end_date', models.DateField(blank=True, null=True)),
                ('production_year', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('task_url', models.URLField(null=True, blank=True, help_text='External workflow system URL', max_length=2048)),
                ('loan_end_date', models.DateField(verbose_name='Loan end date', default=None, blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('assets.baseobject',),
        ),
        migrations.AddField(
            model_name='service',
            name='environments',
            field=models.ManyToManyField(through='assets.ServiceEnvironment', to='assets.Environment'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='asset',
            field=models.ForeignKey(related_name='genericcomponent', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='model',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='model', to='assets.ComponentModel', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='componentmodel',
            unique_together=set([('speed', 'cores', 'size', 'type', 'family')]),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(blank=True, to='assets.BaseObject', null=True),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='service_env',
            field=models.ForeignKey(to='assets.ServiceEnvironment', null=True),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='category',
            field=mptt.fields.TreeForeignKey(related_name='models', null=True, to='assets.Category'),
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
            model_name='asset',
            name='model',
            field=models.ForeignKey(to='assets.AssetModel'),
        ),
    ]
