# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.transitions.fields
import ralph.lib.mixins.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('assets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackOfficeAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(auto_created=True, parent_link=True, serialize=False, to='assets.Asset', primary_key=True)),
                ('location', models.CharField(max_length=128, blank=True, null=True)),
                ('purchase_order', models.CharField(max_length=50, blank=True, null=True)),
                ('loan_end_date', models.DateField(blank=True, default=None, verbose_name='Loan end date', null=True)),
                ('status', ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'installed'), (10, 'free'), (11, 'reserved')])),
                ('imei', ralph.lib.mixins.fields.NullableCharField(max_length=18, blank=True, unique=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Back Office Assets',
                'verbose_name': 'Back Office Asset',
            },
            bases=('assets.asset', models.Model),
        ),
        migrations.CreateModel(
            name='OfficeInfrastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'verbose_name_plural': 'Office Infrastructures',
                'verbose_name': 'Office Infrastructure',
            },
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='office_infrastructure',
            field=models.ForeignKey(blank=True, to='back_office.OfficeInfrastructure', null=True),
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='owner',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, related_name='assets_as_owner', null=True),
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='region',
            field=models.ForeignKey(to='accounts.Region'),
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, related_name='assets_as_user', null=True),
        ),
        migrations.AddField(
            model_name='backofficeasset',
            name='warehouse',
            field=models.ForeignKey(to='back_office.Warehouse', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
