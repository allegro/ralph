# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0010_auto_20210702_1129"),
    ]

    operations = [
        migrations.CreateModel(
            name="TradeMarkKind",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("type", models.CharField(max_length=255)),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
    ]
