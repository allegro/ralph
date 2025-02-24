# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("back_office", "0018_auto_20230206_1020"),
    ]

    operations = [
        migrations.AddField(
            model_name="backofficeasset",
            name="last_status_change",
            field=models.DateField(
                verbose_name="Last status change", blank=True, null=True, default=None
            ),
        ),
    ]
