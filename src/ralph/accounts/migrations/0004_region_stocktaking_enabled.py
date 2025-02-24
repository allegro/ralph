# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_region_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="stocktaking_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
