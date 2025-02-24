# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0012_remove_network_dns_servers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="network",
            name="dns_servers_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="dhcp.DNSServerGroup",
                null=True,
                blank=True,
            ),
        ),
    ]
