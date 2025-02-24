# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0002_auto_20151125_1354"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="report",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="reportlanguage",
            options={"ordering": ["name"]},
        ),
    ]
