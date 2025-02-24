# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0005_network_gateway"),
    ]

    operations = [
        migrations.AddField(
            model_name="networkenvironment",
            name="use_hostname_counter",
            field=models.BooleanField(
                default=True,
                help_text="If set to false hostname based on already added hostnames.",
            ),
        ),
    ]
