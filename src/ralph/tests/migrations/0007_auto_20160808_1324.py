# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests", "0006_auto_20160607_0842"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bar",
            name="date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
