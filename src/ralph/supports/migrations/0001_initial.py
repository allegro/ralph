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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=100, blank=True)),
                ('price', models.DecimalField(null=True, blank=True, decimal_places=2, default=0, max_digits=10)),
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
                ('base_objects', models.ManyToManyField(related_name='supports', to='assets.BaseObject')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='support',
            name='support_type',
            field=models.ForeignKey(blank=True, to='supports.SupportType', null=True, on_delete=django.db.models.deletion.PROTECT, default=None),
        ),
    ]
