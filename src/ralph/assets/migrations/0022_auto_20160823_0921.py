# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0021_auto_20160810_1410"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="invoice_no",
            field=models.CharField(
                null=True,
                blank=True,
                verbose_name="invoice number",
                max_length=128,
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name="asset",
            name="niw",
            field=ralph.lib.mixins.fields.NullableCharField(
                null=True,
                blank=True,
                verbose_name="inventory number",
                default=None,
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="asset",
            name="order_no",
            field=models.CharField(
                null=True, blank=True, max_length=50, verbose_name="order number"
            ),
        ),
    ]
