# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0029_asset_start_usage"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="serviceenvironment",
            options={"ordering": ("service__name", "environment__name")},
        ),
    ]
