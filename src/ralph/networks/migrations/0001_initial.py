# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import mptt.fields
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.mixins.models
import ralph.networks.fields
import ralph.networks.models.networks


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0013_auto_20160606_1438"),
        ("dhcp", "__first__"),
        ("assets", "0012_auto_20160606_1409"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="DiscoveryQueue",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
            ],
            options={
                "verbose_name": "discovery queue",
                "verbose_name_plural": "discovery queues",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="IPAddress",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="last modified"),
                ),
                (
                    "last_seen",
                    models.DateTimeField(verbose_name="last seen", auto_now_add=True),
                ),
                (
                    "address",
                    models.GenericIPAddressField(
                        default=None,
                        null=True,
                        help_text="Presented as string.",
                        verbose_name="IP address",
                        unique=True,
                    ),
                ),
                (
                    "hostname",
                    models.CharField(
                        default=None,
                        null=True,
                        verbose_name="Hostname",
                        blank=True,
                        max_length=255,
                    ),
                ),
                (
                    "number",
                    models.DecimalField(
                        default=None,
                        help_text="Presented as int.",
                        verbose_name="IP address",
                        max_digits=39,
                        editable=False,
                        decimal_places=0,
                        unique=True,
                    ),
                ),
                (
                    "is_management",
                    models.BooleanField(
                        default=False, verbose_name="This is a management address"
                    ),
                ),
                (
                    "is_public",
                    models.BooleanField(
                        default=False,
                        editable=False,
                        verbose_name="This is a public address",
                    ),
                ),
                (
                    "is_gateway",
                    models.BooleanField(
                        default=False,
                        editable=False,
                        verbose_name="This is a gateway address",
                    ),
                ),
                (
                    "status",
                    models.PositiveSmallIntegerField(
                        default=1, choices=[(1, "DHCP (used)"), (2, "reserved")]
                    ),
                ),
                (
                    "base_object",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        to="assets.BaseObject",
                        verbose_name="Base object",
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "IP addresses",
                "verbose_name": "IP address",
            },
            bases=(ralph.networks.models.networks.NetworkMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Network",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
                (
                    "created",
                    models.DateTimeField(
                        verbose_name="date created", auto_now_add=True
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="last modified"),
                ),
                (
                    "address",
                    ralph.networks.fields.IPNetwork(
                        help_text="Presented as string (e.g. 192.168.0.0/24)",
                        verbose_name="network address",
                    ),
                ),
                (
                    "remarks",
                    models.TextField(
                        default="",
                        help_text="Additional information.",
                        verbose_name="remarks",
                        blank=True,
                    ),
                ),
                (
                    "vlan",
                    models.PositiveIntegerField(
                        default=None, null=True, verbose_name="VLAN number", blank=True
                    ),
                ),
                (
                    "min_ip",
                    models.DecimalField(
                        default=None,
                        null=True,
                        editable=False,
                        verbose_name="smallest IP number",
                        blank=True,
                        max_digits=39,
                        decimal_places=0,
                    ),
                ),
                (
                    "max_ip",
                    models.DecimalField(
                        default=None,
                        null=True,
                        editable=False,
                        verbose_name="largest IP number",
                        blank=True,
                        max_digits=39,
                        decimal_places=0,
                    ),
                ),
                (
                    "dhcp_broadcast",
                    models.BooleanField(
                        default=False,
                        db_index=True,
                        verbose_name="Broadcast in DHCP configuration",
                    ),
                ),
                ("lft", models.PositiveIntegerField(db_index=True, editable=False)),
                ("rght", models.PositiveIntegerField(db_index=True, editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                "verbose_name_plural": "networks",
                "verbose_name": "network",
            },
            bases=(
                ralph.lib.mixins.models.AdminAbsoluteUrlMixin,
                ralph.networks.models.networks.NetworkMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="NetworkEnvironment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
                (
                    "hosts_naming_template",
                    models.CharField(
                        help_text="E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc",
                        verbose_name="hosts naming template",
                        max_length=30,
                    ),
                ),
                (
                    "next_server",
                    models.CharField(
                        default="",
                        help_text="The address for a TFTP server for DHCP.",
                        verbose_name="next server",
                        blank=True,
                        max_length=32,
                    ),
                ),
                (
                    "domain",
                    models.CharField(
                        null=True, verbose_name="domain", blank=True, max_length=255
                    ),
                ),
                (
                    "remarks",
                    models.TextField(
                        null=True,
                        help_text="Additional information.",
                        verbose_name="remarks",
                        blank=True,
                    ),
                ),
                (
                    "data_center",
                    models.ForeignKey(
                        to="data_center.DataCenter",
                        verbose_name="data center",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "queue",
                    models.ForeignKey(
                        null=True,
                        to="networks.DiscoveryQueue",
                        verbose_name="discovery queue",
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="NetworkKind",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
            ],
            options={
                "verbose_name": "network kind",
                "verbose_name_plural": "network kinds",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="NetworkTerminator",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="name", unique=True),
                ),
            ],
            options={
                "verbose_name": "network terminator",
                "verbose_name_plural": "network terminators",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="network",
            name="kind",
            field=models.ForeignKey(
                default=None,
                null=True,
                to="networks.NetworkKind",
                verbose_name="network kind",
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="network_environment",
            field=models.ForeignKey(
                null=True,
                to="networks.NetworkEnvironment",
                verbose_name="environment",
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="parent",
            field=mptt.fields.TreeForeignKey(
                null=True,
                editable=False,
                blank=True,
                to="networks.Network",
                related_name="children",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="racks",
            field=models.ManyToManyField(
                to="data_center.Rack", verbose_name="racks", blank=True
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="terminators",
            field=models.ManyToManyField(
                to="networks.NetworkTerminator",
                verbose_name="network terminators",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="network",
            field=models.ForeignKey(
                default=None,
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.SET_NULL,
                to="networks.Network",
                related_name="ips",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="network",
            unique_together=set([("min_ip", "max_ip")]),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
