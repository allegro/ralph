# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers
import ralph.lib.mixins.models
import ralph.lib.mixins.fields
from django.conf import settings
import django.db.models.deletion
import django.core.validators
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetHolder',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssetLastHostname',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('prefix', models.CharField(max_length=8, db_index=True)),
                ('counter', models.PositiveIntegerField(default=1)),
                ('postfix', models.CharField(max_length=8, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetModel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('type', models.PositiveIntegerField(verbose_name='type', choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')])),
                ('power_consumption', models.PositiveIntegerField(verbose_name='Power consumption', blank=True, default=0)),
                ('height_of_device', models.FloatField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Height of device', blank=True, default=0)),
                ('cores_count', models.PositiveIntegerField(verbose_name='Cores count', blank=True, default=0)),
                ('visualization_layout_front', models.PositiveIntegerField(verbose_name='visualization layout of front side', choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], blank=True, default=1)),
                ('visualization_layout_back', models.PositiveIntegerField(verbose_name='visualization layout of back side', choices=[(1, 'N/A'), (2, '1x2'), (3, '2x8'), (4, '2x16 (A/B)'), (5, '4x2')], blank=True, default=1)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('remarks', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BudgetInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Budgets info',
                'verbose_name': 'Budget info',
            },
        ),
        migrations.CreateModel(
            name='BusinessSegment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('code', models.CharField(max_length=4, blank=True, default='')),
                ('imei_required', models.BooleanField(default=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, null=True, to='assets.Category')),
            ],
            options={
                'verbose_name_plural': 'categories',
                'verbose_name': 'category',
            },
        ),
        migrations.CreateModel(
            name='ComponentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('speed', models.PositiveIntegerField(verbose_name='speed (MHz)', blank=True, default=0)),
                ('cores', models.PositiveIntegerField(verbose_name='number of cores', blank=True, default=0)),
                ('size', models.PositiveIntegerField(verbose_name='size (MiB)', blank=True, default=0)),
                ('type', models.PositiveIntegerField(verbose_name='component type', choices=[(1, 'processor'), (2, 'memory'), (3, 'disk drive'), (4, 'ethernet card'), (5, 'expansion card'), (6, 'fibre channel card'), (7, 'disk share'), (8, 'unknown'), (9, 'management'), (10, 'power module'), (11, 'cooling device'), (12, 'media tray'), (13, 'chassis'), (14, 'backup'), (15, 'software'), (16, 'operating system')], default=8)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=255, verbose_name='label', blank=True, null=True, default=None)),
                ('sn', ralph.lib.mixins.fields.NullableCharField(max_length=255, blank=True, null=True, unique=True, verbose_name='vendor SN', default=None)),
            ],
            options={
                'verbose_name_plural': 'generic components',
                'verbose_name': 'generic component',
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('description', models.TextField(blank=True)),
                ('business_segment', models.ForeignKey(to='assets.BusinessSegment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('uid', ralph.lib.mixins.fields.NullableCharField(max_length=40, unique=True, blank=True, null=True)),
                ('cost_center', models.CharField(max_length=100, blank=True)),
                ('business_owners', models.ManyToManyField(related_name='services_business_owner', to=settings.AUTH_USER_MODEL, blank=True)),
                ('profit_center', models.ForeignKey(blank=True, null=True, to='assets.ProfitCenter')),
                ('support_team', models.ForeignKey(related_name='services', blank=True, null=True, to='accounts.Team')),
                ('technical_owners', models.ManyToManyField(related_name='services_technical_owner', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, to='assets.BaseObject', serialize=False, primary_key=True)),
                ('hostname', models.CharField(max_length=255, verbose_name='hostname', blank=True, null=True, default=None)),
                ('sn', ralph.lib.mixins.fields.NullableCharField(unique=True, max_length=200, verbose_name='SN', blank=True, null=True)),
                ('barcode', ralph.lib.mixins.fields.NullableCharField(max_length=200, blank=True, null=True, unique=True, verbose_name='barcode', default=None)),
                ('niw', ralph.lib.mixins.fields.NullableCharField(max_length=200, verbose_name='Inventory number', blank=True, null=True, default=None)),
                ('required_support', models.BooleanField(default=False)),
                ('order_no', models.CharField(max_length=50, blank=True, null=True)),
                ('invoice_no', models.CharField(max_length=128, db_index=True, blank=True, null=True)),
                ('invoice_date', models.DateField(blank=True, null=True)),
                ('price', models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)),
                ('provider', models.CharField(max_length=100, blank=True, null=True)),
                ('depreciation_rate', models.DecimalField(help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .', decimal_places=2, blank=True, max_digits=5, default=25)),
                ('force_depreciation', models.BooleanField(help_text='Check if you no longer want to bill for this asset')),
                ('depreciation_end_date', models.DateField(blank=True, null=True)),
                ('task_url', models.URLField(help_text='External workflow system URL', max_length=2048, blank=True, null=True)),
                ('budget_info', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='assets.BudgetInfo', default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject'),
        ),
        migrations.CreateModel(
            name='ServiceEnvironment',
            fields=[
                ('baseobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, to='assets.BaseObject', serialize=False, primary_key=True)),
                ('environment', models.ForeignKey(to='assets.Environment')),
                ('service', models.ForeignKey(to='assets.Service')),
            ],
            bases=('assets.baseobject',),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='asset',
            field=models.ForeignKey(related_name='genericcomponent', to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='assets.ComponentModel', verbose_name='model', default=None),
        ),
        migrations.AlterUniqueTogether(
            name='componentmodel',
            unique_together=set([('speed', 'cores', 'size', 'type', 'family')]),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(related_name='children', blank=True, null=True, to='assets.BaseObject'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', blank=True, to='taggit.Tag', through='taggit.TaggedItem', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='category',
            field=mptt.fields.TreeForeignKey(related_name='models', null=True, to='assets.Category'),
        ),
        migrations.AddField(
            model_name='assetmodel',
            name='manufacturer',
            field=models.ForeignKey(blank=True, null=True, to='assets.Manufacturer', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterUniqueTogether(
            name='assetlasthostname',
            unique_together=set([('prefix', 'postfix')]),
        ),
        migrations.AddField(
            model_name='service',
            name='environments',
            field=models.ManyToManyField(to='assets.Environment', through='assets.ServiceEnvironment'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='service_env',
            field=models.ForeignKey(to='assets.ServiceEnvironment', null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='model',
            field=models.ForeignKey(related_name='assets', to='assets.AssetModel'),
        ),
        migrations.AddField(
            model_name='asset',
            name='property_of',
            field=models.ForeignKey(blank=True, null=True, to='assets.AssetHolder', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterUniqueTogether(
            name='serviceenvironment',
            unique_together=set([('service', 'environment')]),
        ),
    ]
