# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Support',
            fields=[
                ('baseobject_ptr', models.OneToOneField(auto_created=True, parent_link=True, to='assets.BaseObject', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=75)),
                ('asset_type', models.PositiveSmallIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], default=4)),
                ('contract_id', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('price', models.DecimalField(blank=True, decimal_places=2, null=True, max_digits=10, default=0)),
                ('date_from', models.DateField(blank=True, null=True)),
                ('date_to', models.DateField()),
                ('escalation_path', models.CharField(blank=True, max_length=200)),
                ('contract_terms', models.TextField(blank=True)),
                ('sla_type', models.CharField(blank=True, max_length=200)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'new')], verbose_name='status', default=1)),
                ('producer', models.CharField(blank=True, max_length=100)),
                ('supplier', models.CharField(blank=True, max_length=100)),
                ('serial_no', models.CharField(blank=True, max_length=100)),
                ('invoice_no', models.CharField(blank=True, max_length=100, db_index=True)),
                ('invoice_date', models.DateField(blank=True, verbose_name='Invoice date', null=True)),
                ('period_in_months', models.IntegerField(blank=True, null=True)),
                ('base_objects', models.ManyToManyField(to='assets.BaseObject', related_name='supports')),
                ('budget_info', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, null=True, to='assets.BudgetInfo', default=None)),
                ('property_of', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, null=True, to='assets.AssetHolder')),
                ('region', models.ForeignKey(to='accounts.Region')),
            ],
            options={
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, 'assets.baseobject', models.Model),
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
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, null=True, to='supports.SupportType', default=None),
        ),
    ]
