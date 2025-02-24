# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.fields
import ralph.lib.mixins.models
import ralph.lib.transitions.fields
import ralph.networks.models.networks


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Accessory",
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
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
            ],
            options={
                "verbose_name": "accessory",
                "verbose_name_plural": "accessories",
            },
        ),
        migrations.CreateModel(
            name="CloudProject",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="Connection",
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
                    "connection_type",
                    models.PositiveIntegerField(
                        verbose_name="connection type",
                        choices=[(1, "network connection")],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Database",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "database",
                "verbose_name_plural": "databases",
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="DataCenter",
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
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "visualization_cols_num",
                    models.PositiveIntegerField(
                        verbose_name="visualization grid columns number", default=20
                    ),
                ),
                (
                    "visualization_rows_num",
                    models.PositiveIntegerField(
                        verbose_name="visualization grid rows number", default=20
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DataCenterAsset",
            fields=[
                (
                    "asset_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.Asset",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "status",
                    ralph.lib.transitions.fields.TransitionField(
                        choices=[
                            (1, "new"),
                            (2, "in use"),
                            (3, "free"),
                            (4, "damaged"),
                            (5, "liquidated"),
                            (6, "to deploy"),
                        ],
                        default=1,
                    ),
                ),
                ("position", models.IntegerField(null=True)),
                (
                    "orientation",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "front"),
                            (2, "back"),
                            (3, "middle"),
                            (101, "left"),
                            (102, "right"),
                        ],
                        default=1,
                    ),
                ),
                (
                    "slot_no",
                    models.CharField(
                        max_length=3,
                        verbose_name="slot number",
                        blank=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_slot_no",
                                message="Slot number should be a number from range 1-16 with an optional postfix 'A' or 'B' (e.g. '16A')",
                                regex=re.compile("^([1-9][A,B]?|1[0-6][A,B]?)$", 32),
                            )
                        ],
                        null=True,
                        help_text="Fill it if asset is blade server",
                    ),
                ),
                (
                    "source",
                    models.PositiveIntegerField(
                        verbose_name="source",
                        choices=[(1, "shipment"), (2, "salvaged")],
                        blank=True,
                        db_index=True,
                        null=True,
                    ),
                ),
                ("delivery_date", models.DateField(blank=True, null=True)),
                (
                    "production_year",
                    models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                ("production_use_date", models.DateField(blank=True, null=True)),
                (
                    "management_ip",
                    models.GenericIPAddressField(
                        default=None,
                        unique=True,
                        verbose_name="Management IP address",
                        blank=True,
                        null=True,
                        help_text="Presented as string.",
                    ),
                ),
                (
                    "management_hostname",
                    ralph.lib.mixins.fields.NullableCharField(
                        blank=True, null=True, unique=True, max_length=100
                    ),
                ),
                (
                    "connections",
                    models.ManyToManyField(
                        through="data_center.Connection",
                        to="data_center.DataCenterAsset",
                    ),
                ),
            ],
            options={
                "verbose_name": "data center asset",
                "verbose_name_plural": "data center assets",
            },
            bases=("assets.asset",),
        ),
        migrations.CreateModel(
            name="DiscoveryQueue",
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
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
            ],
            options={
                "verbose_name": "discovery queue",
                "verbose_name_plural": "discovery queues",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="DiskShare",
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
                    "share_id",
                    models.PositiveIntegerField(
                        verbose_name="share identifier", blank=True, null=True
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        verbose_name="name",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        verbose_name="size (MiB)", blank=True, null=True
                    ),
                ),
                (
                    "snapshot_size",
                    models.PositiveIntegerField(
                        verbose_name="size for snapshots (MiB)", blank=True, null=True
                    ),
                ),
                (
                    "wwn",
                    ralph.lib.mixins.fields.NullableCharField(
                        verbose_name="Volume serial", unique=True, max_length=33
                    ),
                ),
                ("full", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "disk share",
                "verbose_name_plural": "disk shares",
            },
        ),
        migrations.CreateModel(
            name="DiskShareMount",
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
                    "volume",
                    models.CharField(
                        verbose_name="volume",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        verbose_name="size (MiB)", blank=True, null=True
                    ),
                ),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        default=None,
                        verbose_name="asset",
                        to="assets.Asset",
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "share",
                    models.ForeignKey(
                        verbose_name="share",
                        to="data_center.DiskShare",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "disk share mount",
                "verbose_name_plural": "disk share mounts",
            },
        ),
        migrations.CreateModel(
            name="IPAddress",
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
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                (
                    "last_seen",
                    models.DateTimeField(verbose_name="last seen", auto_now_add=True),
                ),
                (
                    "address",
                    models.GenericIPAddressField(
                        default=None,
                        unique=True,
                        verbose_name="IP address",
                        help_text="Presented as string.",
                        null=True,
                    ),
                ),
                (
                    "hostname",
                    models.CharField(
                        verbose_name="Hostname",
                        blank=True,
                        default=None,
                        null=True,
                        max_length=255,
                    ),
                ),
                (
                    "number",
                    models.BigIntegerField(
                        verbose_name="IP address",
                        editable=False,
                        help_text="Presented as int.",
                        unique=True,
                    ),
                ),
                (
                    "is_management",
                    models.BooleanField(
                        verbose_name="This is a management address", default=False
                    ),
                ),
                (
                    "is_public",
                    models.BooleanField(
                        verbose_name="This is a public address",
                        editable=False,
                        default=False,
                    ),
                ),
            ],
            options={
                "verbose_name": "IP address",
                "verbose_name_plural": "IP addresses",
            },
        ),
        migrations.CreateModel(
            name="Network",
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
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "created",
                    models.DateTimeField(verbose_name="date created", auto_now=True),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        verbose_name="last modified", auto_now_add=True
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        verbose_name="network address",
                        help_text="Presented as string (e.g. 192.168.0.0/24)",
                        validators=[ralph.networks.fields.network_validator],
                        unique=True,
                        max_length=18,
                    ),
                ),
                (
                    "gateway",
                    models.GenericIPAddressField(
                        default=None,
                        verbose_name="gateway address",
                        blank=True,
                        null=True,
                        help_text="Presented as string.",
                    ),
                ),
                (
                    "gateway_as_int",
                    models.BigIntegerField(
                        verbose_name="gateway as int",
                        editable=False,
                        blank=True,
                        default=None,
                        null=True,
                    ),
                ),
                (
                    "reserved",
                    models.PositiveIntegerField(
                        verbose_name="reserved",
                        help_text="Number of addresses to be omitted in the automatic determination process, counted from the first in range.",
                        default=10,
                    ),
                ),
                (
                    "reserved_top_margin",
                    models.PositiveIntegerField(
                        verbose_name="reserved (top margin)",
                        help_text="Number of addresses to be omitted in the automatic determination process, counted from the last in range.",
                        default=0,
                    ),
                ),
                (
                    "remarks",
                    models.TextField(
                        verbose_name="remarks",
                        blank=True,
                        default="",
                        help_text="Additional information.",
                    ),
                ),
                (
                    "vlan",
                    models.PositiveIntegerField(
                        verbose_name="VLAN number", blank=True, default=None, null=True
                    ),
                ),
                (
                    "min_ip",
                    models.BigIntegerField(
                        verbose_name="smallest IP number",
                        editable=False,
                        blank=True,
                        default=None,
                        null=True,
                    ),
                ),
                (
                    "max_ip",
                    models.BigIntegerField(
                        verbose_name="largest IP number",
                        editable=False,
                        blank=True,
                        default=None,
                        null=True,
                    ),
                ),
                (
                    "ignore_addresses",
                    models.BooleanField(
                        verbose_name="Ignore addresses from this network",
                        default=False,
                        help_text="Addresses from this network should never be assigned to any device, because they are not unique.",
                    ),
                ),
                (
                    "dhcp_broadcast",
                    models.BooleanField(
                        verbose_name="Broadcast in DHCP configuration",
                        default=False,
                        db_index=True,
                    ),
                ),
                (
                    "dhcp_config",
                    models.TextField(
                        verbose_name="DHCP additional configuration",
                        blank=True,
                        default="",
                    ),
                ),
                (
                    "data_center",
                    models.ForeignKey(
                        verbose_name="data center",
                        to="data_center.DataCenter",
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "network",
                "verbose_name_plural": "networks",
                "ordering": ("vlan",),
            },
        ),
        migrations.CreateModel(
            name="NetworkEnvironment",
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
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
                (
                    "hosts_naming_template",
                    models.CharField(
                        verbose_name="hosts naming template",
                        help_text="E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc h201.dc ... h299.dc h400.dc h401.dc",
                        max_length=30,
                    ),
                ),
                (
                    "next_server",
                    models.CharField(
                        verbose_name="next server",
                        blank=True,
                        default="",
                        help_text="The address for a TFTP server for DHCP.",
                        max_length=32,
                    ),
                ),
                (
                    "domain",
                    models.CharField(
                        verbose_name="domain", blank=True, null=True, max_length=255
                    ),
                ),
                (
                    "remarks",
                    models.TextField(
                        verbose_name="remarks",
                        blank=True,
                        null=True,
                        help_text="Additional information.",
                    ),
                ),
                (
                    "data_center",
                    models.ForeignKey(
                        verbose_name="data center",
                        to="data_center.DataCenter",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "queue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name="discovery queue",
                        to="data_center.DiscoveryQueue",
                        blank=True,
                        null=True,
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
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
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
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", unique=True, max_length=255),
                ),
            ],
            options={
                "verbose_name": "network terminator",
                "verbose_name_plural": "network terminators",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Rack",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
                (
                    "description",
                    models.CharField(
                        verbose_name="description", blank=True, max_length=250
                    ),
                ),
                (
                    "orientation",
                    models.PositiveIntegerField(
                        choices=[(1, "top"), (2, "bottom"), (3, "left"), (4, "right")],
                        default=1,
                    ),
                ),
                ("max_u_height", models.IntegerField(default=48)),
                (
                    "visualization_col",
                    models.PositiveIntegerField(
                        verbose_name="column number on visualization grid", default=0
                    ),
                ),
                (
                    "visualization_row",
                    models.PositiveIntegerField(
                        verbose_name="row number on visualization grid", default=0
                    ),
                ),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="RackAccessory",
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
                    "orientation",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "front"),
                            (2, "back"),
                            (3, "middle"),
                            (101, "left"),
                            (102, "right"),
                        ],
                        default=1,
                    ),
                ),
                ("position", models.IntegerField(null=True)),
                (
                    "remarks",
                    models.CharField(
                        verbose_name="Additional remarks", blank=True, max_length=1024
                    ),
                ),
                (
                    "accessory",
                    models.ForeignKey(
                        to="data_center.Accessory",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "rack",
                    models.ForeignKey(
                        to="data_center.Rack",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "rack accessories",
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ServerRoom",
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
                ("name", models.CharField(verbose_name="name", max_length=75)),
                (
                    "data_center",
                    models.ForeignKey(
                        verbose_name="data center",
                        to="data_center.DataCenter",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="VIP",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "VIP",
                "verbose_name_plural": "VIPs",
            },
            bases=("assets.baseobject",),
        ),
        migrations.CreateModel(
            name="VirtualServer",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        to="assets.BaseObject",
                        auto_created=True,
                        parent_link=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Virtual server (VM)",
                "verbose_name_plural": "Virtual servers (VM)",
            },
            bases=("assets.baseobject",),
        ),
        migrations.AddField(
            model_name="rack",
            name="accessories",
            field=models.ManyToManyField(
                through="data_center.RackAccessory", to="data_center.Accessory"
            ),
        ),
        migrations.AddField(
            model_name="rack",
            name="server_room",
            field=models.ForeignKey(
                verbose_name="server room",
                to="data_center.ServerRoom",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="kind",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                default=None,
                verbose_name="network kind",
                to="data_center.NetworkKind",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="network_environment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="environment",
                to="data_center.NetworkEnvironment",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="racks",
            field=models.ManyToManyField(
                verbose_name="racks", blank=True, to="data_center.Rack"
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="terminators",
            field=models.ManyToManyField(
                verbose_name="network terminators", to="data_center.NetworkTerminator"
            ),
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="base_object",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                default=None,
                verbose_name="Base object",
                to="assets.BaseObject",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="diskshare",
            name="base_object",
            field=models.ForeignKey(
                to="assets.BaseObject",
                related_name="diskshare",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="diskshare",
            name="model",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                default=None,
                verbose_name="model",
                to="assets.ComponentModel",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="datacenterasset",
            name="rack",
            field=models.ForeignKey(
                to="data_center.Rack",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="connection",
            name="inbound",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                verbose_name="connected device",
                to="data_center.DataCenterAsset",
                related_name="inbound_connections",
            ),
        ),
        migrations.AddField(
            model_name="connection",
            name="outbound",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                verbose_name="connected to device",
                to="data_center.DataCenterAsset",
                related_name="outbound_connections",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="rack",
            unique_together=set([("name", "server_room")]),
        ),
        migrations.AlterUniqueTogether(
            name="disksharemount",
            unique_together=set([("share", "asset")]),
        ),
    ]
