# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models

import ralph.lib.mixins.models


class Migration(migrations.Migration):
    dependencies = [
        ("dhcp", "0003_dhcpserver_network_environment"),
    ]

    operations = [
        migrations.CreateModel(
            name="DNSServerGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
            ],
            options={
                "verbose_name": "DNS Server Group",
                "verbose_name_plural": "DNS Server Groups",
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="DNSServerGroupOrder",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("order", models.PositiveIntegerField(db_index=True)),
                (
                    "dns_server",
                    models.ForeignKey(
                        to="dhcp.DNSServer", on_delete=django.db.models.deletion.CASCADE
                    ),
                ),
                (
                    "dns_server_group",
                    models.ForeignKey(
                        to="dhcp.DNSServerGroup",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("order",),
            },
        ),
        migrations.AddField(
            model_name="dnsservergroup",
            name="servers",
            field=models.ManyToManyField(
                through="dhcp.DNSServerGroupOrder", to="dhcp.DNSServer"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="dnsservergrouporder",
            unique_together=set([("dns_server_group", "dns_server")]),
        ),
    ]
