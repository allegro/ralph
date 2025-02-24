# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_auto_20151126_2205"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="assetholder",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="businesssegment",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="environment",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="manufacturer",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="profitcenter",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="service",
            options={"ordering": ["name"]},
        ),
    ]
