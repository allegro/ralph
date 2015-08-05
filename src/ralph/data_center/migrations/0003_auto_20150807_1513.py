# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.fields
import django.core.validators
import re


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0002_auto_20150715_0752'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rackaccessory',
            options={'verbose_name_plural': 'rack accessories'},
        ),
        migrations.RemoveField(
            model_name='datacenterasset',
            name='slots',
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='delivery_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='production_use_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='production_year',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='source',
            field=models.PositiveIntegerField(null=True, db_index=True, blank=True, verbose_name='source', choices=[(1, 'shipment'), (2, 'salvaged')]),
        ),
        migrations.AlterField(
            model_name='datacenterasset',
            name='slot_no',
            field=models.CharField(validators=[django.core.validators.RegexValidator(code='invalid_slot_no', message="Slot number should be a number from range 1-16 with an optional postfix 'A' or 'B' (e.g. '16A')", regex=re.compile('^([1-9][A,B]?|1[0-6][A,B]?)$', 32))], max_length=3, blank=True, verbose_name='slot number', null=True, help_text='Fill it if asset is blade server'),
        ),
        migrations.AlterField(
            model_name='diskshare',
            name='wwn',
            field=ralph.lib.mixins.fields.NullableCharField(unique=True, max_length=33, verbose_name='Volume serial'),
        ),
    ]
