# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_auto_20151204_0758"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportlanguage",
            name="default",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
