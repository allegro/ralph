# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Support',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('price', models.DecimalField(null=True, decimal_places=2, blank=True, default=0, max_digits=10)),
                ('date_from', models.DateField(null=True, blank=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(blank=True, max_length=200)),
                ('contract_terms', models.CharField(blank=True, max_length=200)),
                ('remarks', models.TextField(blank=True)),
                ('sla_type', models.CharField(blank=True, max_length=200)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'new')], verbose_name='status', default=1)),
                ('producer', models.CharField(blank=True, max_length=100)),
                ('supplier', models.CharField(blank=True, max_length=100)),
                ('serial_no', models.CharField(blank=True, max_length=100)),
                ('invoice_no', models.CharField(blank=True, db_index=True, max_length=100)),
                ('invoice_date', models.DateField(null=True, verbose_name='Invoice date', blank=True)),
                ('period_in_months', models.IntegerField(null=True, blank=True)),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', related_name='supports')),
                ('region', models.ForeignKey(to='accounts.Region')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='support',
            name='support_type',
            field=models.ForeignKey(null=True, to='supports.SupportType', default=None, on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
    ]
