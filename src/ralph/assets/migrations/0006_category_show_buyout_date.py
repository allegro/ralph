# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0005_category_depreciation_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="show_buyout_date",
            field=models.BooleanField(default=False),
        ),
    ]
