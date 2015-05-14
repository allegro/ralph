# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


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
            model_name='asset',
            name='model',
            field=models.ForeignKey(to='assets.AssetModel'),
        ),
    ]
