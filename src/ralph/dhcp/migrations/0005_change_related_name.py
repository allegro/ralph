# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dhcp", "0004_add_dns_server_group"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dnsservergrouporder",
            name="dns_server",
            field=models.ForeignKey(
                to="dhcp.DNSServer",
                related_name="server_group_order",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="dnsservergrouporder",
            name="dns_server_group",
            field=models.ForeignKey(
                to="dhcp.DNSServerGroup",
                related_name="server_group_order",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
