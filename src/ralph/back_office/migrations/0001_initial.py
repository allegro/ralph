# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.transitions.fields
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackOfficeAsset',
            fields=[
                ('asset_ptr', models.OneToOneField(to='assets.Asset', auto_created=True, serialize=False, parent_link=True, primary_key=True)),
                ('location', models.CharField(null=True, blank=True, max_length=128)),
                ('purchase_order', models.CharField(null=True, blank=True, max_length=50)),
                ('loan_end_date', models.DateField(null=True, verbose_name='Loan end date', blank=True, default=None)),
                ('status', ralph.lib.transitions.fields.TransitionField(choices=[(1, 'new'), (2, 'in progress'), (3, 'waiting for release'), (4, 'in use'), (5, 'loan'), (6, 'damaged'), (7, 'liquidated'), (8, 'in service'), (9, 'in repair'), (10, 'ok'), (11, 'to deploy')], default=1)),
                ('owner', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='assets_as_owner')),
                ('region', models.ForeignKey(to='accounts.Region')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='assets_as_user')),
            ],
            options={
                'verbose_name': 'Back Office Asset',
                'verbose_name_plural': 'Back Office Assets',
            },
            bases=('assets.asset', models.Model),
        ),
        migrations.CreateModel(
            name='Warehouse',
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
        migrations.AddField(
            model_name='backofficeasset',
            name='warehouse',
            field=models.ForeignKey(to='back_office.Warehouse', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
