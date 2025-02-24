# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0012_populate_trademark_kinds"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trademark",
            name="type",
            field=models.ForeignKey(
                verbose_name="Trade Mark type",
                related_name="trademarks",
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="trade_marks.TradeMarkKind",
            ),
        ),
    ]
