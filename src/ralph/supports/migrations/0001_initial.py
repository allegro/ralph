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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=100, blank=True)),
                ('price', models.DecimalField(max_digits=10, null=True, decimal_places=2, blank=True, default=0)),
                ('date_from', models.DateField(null=True, blank=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(max_length=200, blank=True)),
                ('contract_terms', models.CharField(max_length=200, blank=True)),
                ('additional_notes', models.CharField(max_length=200, blank=True)),
                ('sla_type', models.CharField(max_length=200, blank=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'new')], default=1, verbose_name='status')),
                ('producer', models.CharField(max_length=100, blank=True)),
                ('supplier', models.CharField(max_length=100, blank=True)),
                ('serial_no', models.CharField(max_length=100, blank=True)),
                ('invoice_no', models.CharField(db_index=True, max_length=100, blank=True)),
                ('invoice_date', models.DateField(null=True, blank=True, verbose_name='Invoice date')),
                ('period_in_months', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportType',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='support',
            name='support_type',
            field=models.ForeignKey(default=None, null=True, blank=True, to='supports.SupportType', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
