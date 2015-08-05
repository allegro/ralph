# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_auto_20150721_1402'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='delivery_date',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='loan_end_date',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='production_use_date',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='production_year',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='provider_order_date',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='purchase_order',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='request_date',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='source',
        ),
        migrations.AddField(
            model_name='service',
            name='uid',
            field=ralph.lib.mixins.fields.NullableCharField(max_length=40, null=True, unique=True, blank=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='barcode',
            field=ralph.lib.mixins.fields.NullableCharField(default=None, unique=True, verbose_name='barcode', max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='hostname',
            field=models.CharField(default=None, verbose_name='hostname', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='niw',
            field=ralph.lib.mixins.fields.NullableCharField(default=None, verbose_name='Inventory number', max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='sn',
            field=ralph.lib.mixins.fields.NullableCharField(verbose_name='SN', max_length=200, null=True, unique=True, blank=True),
        ),
        migrations.AlterField(
            model_name='genericcomponent',
            name='sn',
            field=ralph.lib.mixins.fields.NullableCharField(default=None, unique=True, verbose_name='vendor SN', max_length=255, null=True, blank=True),
        ),
    ]
