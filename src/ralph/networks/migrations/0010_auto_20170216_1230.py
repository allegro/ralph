# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0009_auto_20160823_0921"),
    ]

    operations = [
        migrations.AlterField(
            model_name="network",
            name="gateway",
            field=models.ForeignKey(
                to="networks.IPAddress",
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="Gateway address",
                null=True,
                related_name="gateway_network",
            ),
        ),
    ]
