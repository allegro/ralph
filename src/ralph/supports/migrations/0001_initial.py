# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Support',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('price', models.DecimalField(default=0, max_digits=10, decimal_places=2, blank=True, null=True)),
                ('date_from', models.DateField(blank=True, null=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(blank=True, max_length=200)),
                ('contract_terms', models.CharField(blank=True, max_length=200)),
                ('additional_notes', models.CharField(blank=True, max_length=200)),
                ('sla_type', models.CharField(blank=True, max_length=200)),
                ('status', models.PositiveSmallIntegerField(verbose_name='status', default=1, choices=[(1, 'new')])),
                ('producer', models.CharField(blank=True, max_length=100)),
                ('supplier', models.CharField(blank=True, max_length=100)),
                ('serial_no', models.CharField(blank=True, max_length=100)),
                ('invoice_no', models.CharField(db_index=True, blank=True, max_length=100)),
                ('invoice_date', models.DateField(verbose_name='Invoice date', blank=True, null=True)),
                ('period_in_months', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='support',
            name='support_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, default=None, to='supports.SupportType', null=True),
        ),
    ]
