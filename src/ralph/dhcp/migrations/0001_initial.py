# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DHCPServer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "ip",
                    models.GenericIPAddressField(
                        verbose_name="IP address", unique=True
                    ),
                ),
                ("last_synchronized", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "DHCP Server",
                "verbose_name_plural": "DHCP Servers",
            },
        ),
        migrations.CreateModel(
            name="DNSServer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        verbose_name="IP address", unique=True
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        verbose_name="is default", db_index=True, default=False
                    ),
                ),
            ],
            options={
                "verbose_name": "DNS Server",
                "verbose_name_plural": "DNS Servers",
            },
        ),
    ]
