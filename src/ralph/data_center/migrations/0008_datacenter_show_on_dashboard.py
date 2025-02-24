# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0007_auto_20160225_1818"),
    ]

    operations = [
        migrations.AddField(
            model_name="datacenter",
            name="show_on_dashboard",
            field=models.BooleanField(default=True),
        ),
    ]
