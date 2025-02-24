# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import mptt.fields
from django.db import migrations, models

import ralph.networks.fields


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0010_visualization_fields_for_serverroom"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="network",
            options={"verbose_name": "network", "verbose_name_plural": "networks"},
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="is_gateway",
            field=models.BooleanField(
                default=False, verbose_name="This is a gateway address", editable=False
            ),
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="network",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                default=None,
                related_name="ips",
                to="data_center.Network",
                editable=False,
            ),
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="status",
            field=models.PositiveSmallIntegerField(
                default=1, choices=[(1, "DHCP (used)"), (2, "reserved")]
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="level",
            field=models.PositiveIntegerField(default=0, db_index=True, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="network",
            name="lft",
            field=models.PositiveIntegerField(default=0, db_index=True, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="network",
            name="parent",
            field=mptt.fields.TreeForeignKey(
                blank=True,
                null=True,
                related_name="children",
                to="data_center.Network",
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="rght",
            field=models.PositiveIntegerField(default=0, db_index=True, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="network",
            name="tree_id",
            field=models.PositiveIntegerField(default=0, db_index=True, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="number",
            field=models.DecimalField(
                decimal_places=0,
                help_text="Presented as int.",
                verbose_name="IP address",
                default=None,
                unique=True,
                editable=False,
                max_digits=39,
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="address",
            field=ralph.networks.fields.IPNetwork(
                verbose_name="network address",
                help_text="Presented as string (e.g. 192.168.0.0/24)",
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="max_ip",
            field=models.DecimalField(
                blank=True,
                null=True,
                default=None,
                verbose_name="largest IP number",
                decimal_places=0,
                editable=False,
                max_digits=39,
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="min_ip",
            field=models.DecimalField(
                blank=True,
                null=True,
                default=None,
                verbose_name="smallest IP number",
                decimal_places=0,
                editable=False,
                max_digits=39,
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="terminators",
            field=models.ManyToManyField(
                verbose_name="network terminators",
                blank=True,
                to="data_center.NetworkTerminator",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="network",
            unique_together=set([("min_ip", "max_ip")]),
        ),
        migrations.RemoveField(
            model_name="network",
            name="data_center",
        ),
        migrations.RemoveField(
            model_name="network",
            name="dhcp_config",
        ),
        migrations.RemoveField(
            model_name="network",
            name="gateway",
        ),
        migrations.RemoveField(
            model_name="network",
            name="gateway_as_int",
        ),
        migrations.RemoveField(
            model_name="network",
            name="ignore_addresses",
        ),
        migrations.RemoveField(
            model_name="network",
            name="reserved",
        ),
        migrations.RemoveField(
            model_name="network",
            name="reserved_top_margin",
        ),
    ]
