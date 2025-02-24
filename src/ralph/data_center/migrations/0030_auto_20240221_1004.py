# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0029_auto_20230920_1102"),
    ]

    operations = [
        migrations.AddField(
            model_name="datacenterasset",
            name="leasing_rate",
            field=models.FloatField(
                verbose_name="Vendor contact number", blank=True, null=True
            ),
        ),
        migrations.AddField(
            model_name="datacenterasset",
            name="vendor_contract_number",
            field=models.CharField(
                verbose_name="Vendor contract number",
                max_length=256,
                blank=True,
                null=True,
            ),
        ),
    ]
