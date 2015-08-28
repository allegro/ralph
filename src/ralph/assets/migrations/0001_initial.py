# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.fields
import mptt.fields
import ralph.lib.mixins.models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetLastHostname',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('prefix', models.CharField(db_index=True, max_length=8)),
                ('counter', models.PositiveIntegerField(default=1)),
                ('postfix', models.CharField(db_index=True, max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='AssetModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('type', models.PositiveIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], verbose_name='type')),
                ('power_consumption', models.IntegerField(verbose_name='Power consumption', blank=True, default=0)),
                ('height_of_device', models.FloatField(verbose_name='Height of device', blank=True, default=0)),
                ('cores_count', models.IntegerField(verbose_name='Cores count', blank=True, default=0)),
                ('visualization_layout_front', models.PositiveIntegerField(choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], verbose_name='visualization layout of front side', blank=True, default=1)),
                ('visualization_layout_back', models.PositiveIntegerField(choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], verbose_name='visualization layout of back side', blank=True, default=1)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('remarks', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BusinessSegment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('code', models.CharField(blank=True, default='', max_length=4)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(null=True, to='assets.Category', blank=True, related_name='children')),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='ComponentModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('speed', models.PositiveIntegerField(verbose_name='speed (MHz)', blank=True, default=0)),
                ('cores', models.PositiveIntegerField(verbose_name='number of cores', blank=True, default=0)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, default=0)),
                ('type', models.PositiveIntegerField(choices=[(1, 'processor'), (2, 'memory'), (3, 'disk drive'), (4, 'ethernet card'), (5, 'expansion card'), (6, 'fibre channel card'), (7, 'disk share'), (8, 'unknown'), (9, 'management'), (10, 'power module'), (11, 'cooling device'), (12, 'media tray'), (13, 'chassis'), (14, 'backup'), (15, 'software'), (16, 'operating system')], verbose_name='component type', default=8)),
                ('family', models.CharField(blank=True, default='', max_length=128)),
            ],
            options={
                'verbose_name': 'component model',
                'verbose_name_plural': 'component models',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('label', models.CharField(null=True, verbose_name='label', blank=True, default=None, max_length=255)),
                ('sn', ralph.lib.mixins.fields.NullableCharField(null=True, verbose_name='vendor SN', default=None, unique=True, blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'generic component',
                'verbose_name_plural': 'generic components',
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProfitCenter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('business_segment', models.ForeignKey(to='assets.BusinessSegment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('uid', ralph.lib.mixins.fields.NullableCharField(null=True, blank=True, max_length=40, unique=True)),
                ('cost_center', models.CharField(blank=True, max_length=100)),
                ('business_owners', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='services_business_owner')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('environment', models.ForeignKey(to='assets.Environment')),
                ('service', models.ForeignKey(to='assets.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('baseobject_ptr', models.OneToOneField(to='assets.BaseObject', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
                ('hostname', models.CharField(null=True, verbose_name='hostname', blank=True, default=None, max_length=255)),
                ('sn', ralph.lib.mixins.fields.NullableCharField(null=True, verbose_name='SN', max_length=200, blank=True, unique=True)),
                ('barcode', ralph.lib.mixins.fields.NullableCharField(null=True, verbose_name='barcode', default=None, unique=True, blank=True, max_length=200)),
                ('niw', ralph.lib.mixins.fields.NullableCharField(null=True, verbose_name='Inventory number', blank=True, default=None, max_length=200)),
                ('required_support', models.BooleanField(default=False)),
                ('order_no', models.CharField(null=True, blank=True, max_length=50)),
                ('invoice_no', models.CharField(null=True, blank=True, db_index=True, max_length=128)),
                ('invoice_date', models.DateField(null=True, blank=True)),
                ('price', models.DecimalField(null=True, decimal_places=2, blank=True, default=0, max_digits=10)),
                ('provider', models.CharField(null=True, blank=True, max_length=100)),
                ('depreciation_rate', models.DecimalField(help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .', blank=True, default=25, max_digits=5, decimal_places=2)),
                ('force_depreciation', models.BooleanField(help_text='Check if you no longer want to bill for this asset')),
                ('depreciation_end_date', models.DateField(null=True, blank=True)),
                ('task_url', models.URLField(null=True, help_text='External workflow system URL', blank=True, max_length=2048)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject'),
        ),
        migrations.AddField(
            model_name='service',
            name='environments',
            field=models.ManyToManyField(to='assets.Environment', through='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='service',
            name='profit_center',
            field=models.ForeignKey(null=True, to='assets.ProfitCenter', blank=True),
        ),
        migrations.AddField(
            model_name='service',
            name='technical_owners',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='services_technical_owner'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='asset',
            field=models.ForeignKey(to='assets.BaseObject', related_name='genericcomponent'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='model',
            field=models.ForeignKey(null=True, to='assets.ComponentModel', verbose_name='model', default=None, on_delete=django.db.models.deletion.SET_NULL, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='componentmodel',
            unique_together=set([('speed', 'cores', 'size', 'type', 'family')]),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='content_type',
            field=models.ForeignKey(null=True, to='contenttypes.ContentType', blank=True),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(null=True, to='assets.BaseObject', blank=True),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='service_env',
            field=models.ForeignKey(null=True, to='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='category',
            field=mptt.fields.TreeForeignKey(null=True, to='assets.Category', related_name='models'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='manufacturer',
            field=models.ForeignKey(null=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='assetlasthostname',
            unique_together=set([('prefix', 'postfix')]),
        ),
        migrations.AlterUniqueTogether(
            name='serviceenvironment',
            unique_together=set([('service', 'environment')]),
        ),
        migrations.AddField(
            model_name='asset',
            name='model',
            field=models.ForeignKey(to='assets.AssetModel', related_name='assets'),
        ),
    ]
