# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetLastHostname',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('prefix', models.CharField(db_index=True, max_length=8)),
                ('counter', models.PositiveIntegerField(default=1)),
                ('postfix', models.CharField(db_index=True, max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='AssetModel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('type', models.PositiveIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], verbose_name='type')),
                ('power_consumption', models.IntegerField(blank=True, default=0, verbose_name='Power consumption')),
                ('height_of_device', models.FloatField(blank=True, default=0, verbose_name='Height of device')),
                ('cores_count', models.IntegerField(blank=True, default=0, verbose_name='Cores count')),
                ('visualization_layout_front', models.PositiveIntegerField(choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], blank=True, default=1, verbose_name='visualization layout of front side')),
                ('visualization_layout_back', models.PositiveIntegerField(choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], blank=True, default=1, verbose_name='visualization layout of back side')),
                ('has_parent', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'models',
                'verbose_name': 'model',
            },
        ),
        migrations.CreateModel(
            name='BaseObject',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('code', models.CharField(max_length=4, blank=True, default='')),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', null=True, blank=True, to='assets.Category')),
            ],
            options={
                'verbose_name_plural': 'categories',
                'verbose_name': 'category',
            },
        ),
        migrations.CreateModel(
            name='ComponentModel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('speed', models.PositiveIntegerField(blank=True, default=0, verbose_name='speed (MHz)')),
                ('cores', models.PositiveIntegerField(blank=True, default=0, verbose_name='number of cores')),
                ('size', models.PositiveIntegerField(blank=True, default=0, verbose_name='size (MiB)')),
                ('type', models.PositiveIntegerField(choices=[(1, 'processor'), (2, 'memory'), (3, 'disk drive'), (4, 'ethernet card'), (5, 'expansion card'), (6, 'fibre channel card'), (7, 'disk share'), (8, 'unknown'), (9, 'management'), (10, 'power module'), (11, 'cooling device'), (12, 'media tray'), (13, 'chassis'), (14, 'backup'), (15, 'software'), (16, 'operating system')], default=8, verbose_name='component type')),
                ('family', models.CharField(max_length=128, blank=True, default='')),
            ],
            options={
                'verbose_name_plural': 'component models',
                'verbose_name': 'component model',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('label', models.CharField(null=True, max_length=255, blank=True, default=None, verbose_name='label')),
                ('sn', models.CharField(default=None, null=True, unique=True, max_length=255, blank=True, verbose_name='vendor SN')),
            ],
            options={
                'verbose_name_plural': 'generic components',
                'verbose_name': 'generic component',
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('environment', models.ForeignKey(to='assets.Environment')),
                ('service', models.ForeignKey(to='assets.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('baseobject_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, to='assets.BaseObject', auto_created=True)),
                ('hostname', models.CharField(null=True, max_length=255, blank=True, default=None)),
                ('niw', models.CharField(null=True, max_length=200, blank=True, default=None, verbose_name='Inventory number')),
                ('invoice_no', models.CharField(db_index=True, null=True, max_length=128, blank=True)),
                ('required_support', models.BooleanField(default=False)),
                ('order_no', models.CharField(null=True, max_length=50, blank=True)),
                ('purchase_order', models.CharField(null=True, max_length=50, blank=True)),
                ('invoice_date', models.DateField(null=True, blank=True)),
                ('sn', models.CharField(null=True, unique=True, max_length=200, blank=True)),
                ('barcode', models.CharField(null=True, unique=True, max_length=200, blank=True, default=None)),
                ('price', models.DecimalField(max_digits=10, null=True, decimal_places=2, blank=True, default=0)),
                ('provider', models.CharField(null=True, max_length=100, blank=True)),
                ('source', models.PositiveIntegerField(db_index=True, null=True, choices=[(1, 'shipment'), (2, 'salvaged')], blank=True, verbose_name='source')),
                ('status', models.PositiveSmallIntegerField(null=True, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')], blank=True, default=1, verbose_name='status')),
                ('request_date', models.DateField(null=True, blank=True)),
                ('delivery_date', models.DateField(null=True, blank=True)),
                ('production_use_date', models.DateField(null=True, blank=True)),
                ('provider_order_date', models.DateField(null=True, blank=True)),
                ('deprecation_rate', models.DecimalField(help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .', max_digits=5, decimal_places=2, blank=True, default=25)),
                ('force_deprecation', models.BooleanField(help_text='Check if you no longer want to bill for this asset')),
                ('deprecation_end_date', models.DateField(null=True, blank=True)),
                ('production_year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('task_url', models.URLField(null=True, max_length=2048, blank=True, help_text='External workflow system URL')),
                ('loan_end_date', models.DateField(null=True, blank=True, default=None, verbose_name='Loan end date')),
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
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='assets.ComponentModel', verbose_name='model'),
        ),
        migrations.AlterUniqueTogether(
            name='componentmodel',
            unique_together=set([('speed', 'cores', 'size', 'type', 'family')]),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(null=True, blank=True, to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='service_env',
            field=models.ForeignKey(null=True, to='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='category',
            field=mptt.fields.TreeForeignKey(related_name='models', null=True, to='assets.Category'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='manufacturer',
            field=models.ForeignKey(null=True, blank=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT),
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
