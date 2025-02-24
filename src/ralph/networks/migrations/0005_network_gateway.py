# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0004_auto_20160606_1512"),
    ]

    operations = [
        migrations.AddField(
            model_name="network",
            name="gateway",
            field=models.ForeignKey(
                to="networks.IPAddress",
                null=True,
                verbose_name="Gateway address",
                blank=True,
                related_name="gateway_network",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
