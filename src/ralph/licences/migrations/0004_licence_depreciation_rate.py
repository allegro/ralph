# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0003_auto_20160823_0921"),
    ]

    operations = [
        migrations.AddField(
            model_name="licence",
            name="depreciation_rate",
            field=models.DecimalField(
                help_text='This value is in percentage. For example value: "100" means it depreciates during a year. Value: "25" means it depreciates during 4 years, and so on... .',
                default=50,
                null=True,
                decimal_places=2,
                max_digits=5,
                blank=True,
            ),
        ),
    ]
