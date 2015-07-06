# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Support',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=100, blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True, default=0)),
                ('date_from', models.DateField(blank=True, null=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(max_length=200, blank=True)),
                ('contract_terms', models.CharField(max_length=200, blank=True)),
                ('additional_notes', models.CharField(max_length=200, blank=True)),
                ('sla_type', models.CharField(max_length=200, blank=True)),
                ('status', models.PositiveSmallIntegerField(verbose_name='status', choices=[(1, 'new')], default=1)),
                ('producer', models.CharField(max_length=100, blank=True)),
                ('supplier', models.CharField(max_length=100, blank=True)),
                ('serial_no', models.CharField(max_length=100, blank=True)),
                ('invoice_no', models.CharField(max_length=100, db_index=True, blank=True)),
                ('invoice_date', models.DateField(verbose_name='Invoice date', blank=True, null=True)),
                ('period_in_months', models.IntegerField(blank=True, null=True)),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', related_name='supports')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='support',
            name='support_type',
            field=models.ForeignKey(to='supports.SupportType', on_delete=django.db.models.deletion.PROTECT, null=True, blank=True, default=None),
        ),
    ]
