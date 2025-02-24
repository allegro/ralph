# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0013_auto_20171006_0947"),
    ]

    operations = [
        migrations.AlterField(
            model_name="network",
            name="dns_servers_group",
            field=models.ForeignKey(
                to="dhcp.DNSServerGroup",
                related_name="networks",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
            ),
        ),
    ]
