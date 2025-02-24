# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0003_auto_20151204_0758"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouse",
            name="stocktaking_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
