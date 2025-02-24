# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboards", "0002_auto_20170509_1404"),
    ]

    operations = [
        migrations.AddField(
            model_name="graph",
            name="push_to_statsd",
            field=models.BooleanField(
                default=False, help_text="Push graph's data to statsd."
            ),
        ),
    ]
