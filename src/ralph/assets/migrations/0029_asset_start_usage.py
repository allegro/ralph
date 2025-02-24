# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0028_auto_20180730_1135"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="start_usage",
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Fill it if date of first usage is different then date of creation",
            ),
        ),
    ]
