# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ipaddress",
            name="ethernet",
            field=models.OneToOneField(
                to="assets.Ethernet",
                default=None,
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
