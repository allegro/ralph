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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=75, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('price', models.DecimalField(blank=True, max_digits=10, default=0, decimal_places=2, null=True)),
                ('date_from', models.DateField(blank=True, null=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(blank=True, max_length=200)),
                ('contract_terms', models.CharField(blank=True, max_length=200)),
                ('additional_notes', models.CharField(blank=True, max_length=200)),
                ('sla_type', models.CharField(blank=True, max_length=200)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'new')], default=1, verbose_name='status')),
                ('producer', models.CharField(blank=True, max_length=100)),
                ('supplier', models.CharField(blank=True, max_length=100)),
                ('serial_no', models.CharField(blank=True, max_length=100)),
                ('invoice_no', models.CharField(db_index=True, blank=True, max_length=100)),
                ('invoice_date', models.DateField(null=True, blank=True, verbose_name='Invoice date')),
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
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=None, null=True, to='supports.SupportType', blank=True),
        ),
    ]
