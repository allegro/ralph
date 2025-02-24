# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0032_auto_20200909_1012"),
        ("sim_cards", "0003_auto_20181212_1254"),
    ]

    operations = [
        migrations.AddField(
            model_name="simcard",
            name="property_of",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="assets.AssetHolder",
            ),
        ),
    ]
