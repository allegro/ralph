# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0013_auto_20211206_1400"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trademark",
            name="type",
            field=models.ForeignKey(
                verbose_name="Trade Mark type",
                default=2,
                related_name="trademarks",
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="trade_marks.TradeMarkKind",
            ),
        ),
    ]
