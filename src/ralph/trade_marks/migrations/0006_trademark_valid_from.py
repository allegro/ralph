# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0005_auto_20190312_0931"),
    ]

    operations = [
        migrations.AddField(
            model_name="trademark",
            name="valid_from",
            field=models.DateField(blank=True, null=True),
        ),
    ]
