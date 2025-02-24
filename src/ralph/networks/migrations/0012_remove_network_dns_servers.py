# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0011_add_dns_servers_group"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="network",
            name="dns_servers",
        ),
    ]
