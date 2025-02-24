# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0004_licence_depreciation_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="licence",
            name="start_usage",
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Fill it if date of first usage is different then date of creation",
            ),
        ),
    ]
