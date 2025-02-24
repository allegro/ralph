# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0006_trademark_valid_from"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trademark",
            name="valid_to",
            field=models.DateField(blank=True, null=True),
        ),
    ]
