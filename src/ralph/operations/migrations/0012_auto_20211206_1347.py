# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0011_operation_reporter"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="operationstatus",
            options={"verbose_name_plural": "Operation statuses"},
        ),
    ]
