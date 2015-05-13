# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackOfficeAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='assets.Asset')),
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
                ('location', models.CharField(max_length=128, null=True, blank=True)),
                ('owner', models.ForeignKey(related_name='assets_as_owner', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='assets_as_user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'BO Asset',
                'verbose_name_plural': 'BO Assets',
            },
            bases=('assets.asset', models.Model),
        ),
        migrations.CreateModel(
            name='Warehouse',
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
        migrations.AddField(
            model_name='backofficeasset',
            name='warehouse',
            field=models.ForeignKey(to='backoffice.Warehouse', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
