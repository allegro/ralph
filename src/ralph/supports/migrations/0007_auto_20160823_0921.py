# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("supports", "0006_auto_20160615_0805"),
    ]

    operations = [
        migrations.AlterField(
            model_name="support",
            name="contract_id",
            field=models.CharField(max_length=50, verbose_name="contract ID"),
        ),
        migrations.AlterField(
            model_name="support",
            name="invoice_date",
            field=models.DateField(null=True, blank=True, verbose_name="invoice date"),
        ),
        migrations.AlterField(
            model_name="support",
            name="invoice_no",
            field=models.CharField(
                blank=True, verbose_name="invoice number", max_length=100, db_index=True
            ),
        ),
        migrations.AlterField(
            model_name="support",
            name="serial_no",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="serial number"
            ),
        ),
    ]
