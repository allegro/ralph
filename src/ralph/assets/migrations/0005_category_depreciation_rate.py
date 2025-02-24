# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0004_auto_20151204_0758"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="default_depreciation_rate",
            field=models.DecimalField(
                help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .',
                decimal_places=2,
                max_digits=5,
                blank=True,
                default=25,
            ),
        ),
    ]
