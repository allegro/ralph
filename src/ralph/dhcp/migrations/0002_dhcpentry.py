# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0001_initial"),
        ("dhcp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DHCPEntry",
            fields=[],
            options={
                "proxy": True,
            },
            bases=("networks.ipaddress",),
        ),
    ]
