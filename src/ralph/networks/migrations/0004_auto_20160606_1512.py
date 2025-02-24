# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import django.db.models.deletion
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):
    dependencies = [
        ("dhcp", "0002_dhcpentry"),
        ("assets", "0012_auto_20160606_1409"),
        ("networks", "0003_custom_link_ips_to_eth"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ipaddress",
            name="base_object",
        ),
        migrations.RemoveField(
            model_name="networkenvironment",
            name="hosts_naming_template",
        ),
        migrations.RemoveField(
            model_name="networkenvironment",
            name="next_server",
        ),
        migrations.AddField(
            model_name="ipaddress",
            name="dhcp_expose",
            field=models.BooleanField(default=False, verbose_name="Expose in DHCP"),
        ),
        migrations.AddField(
            model_name="network",
            name="dns_servers",
            field=models.ManyToManyField(
                to="dhcp.DNSServer", blank=True, verbose_name="DNS servers"
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="service_env",
            field=models.ForeignKey(
                to="assets.ServiceEnvironment",
                related_name="networks",
                default=None,
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="networkenvironment",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name="date created",
                default=datetime.datetime(2016, 6, 6, 15, 11, 14, 733956),
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="networkenvironment",
            name="hostname_template_counter_length",
            field=models.PositiveIntegerField(
                default=4, verbose_name="hostname template counter length"
            ),
        ),
        migrations.AddField(
            model_name="networkenvironment",
            name="hostname_template_postfix",
            field=models.CharField(
                default="",
                max_length=30,
                verbose_name="hostname template postfix",
                help_text='This value will be used as a postfix when generating new hostname in this network environment. For example, when prefix is "s1", postfix is ".mydc.net" and counter length is 4, following  hostnames will be generated: s10000.mydc.net, s10001.mydc.net, .., s19999.mydc.net.',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="networkenvironment",
            name="hostname_template_prefix",
            field=models.CharField(
                default="", max_length=30, verbose_name="hostname template prefix"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="networkenvironment",
            name="modified",
            field=models.DateTimeField(
                auto_now=True,
                verbose_name="last modified",
                default=datetime.datetime(2016, 6, 6, 15, 11, 34, 653279),
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="address",
            field=models.GenericIPAddressField(
                default="0.0.0.0",
                unique=True,
                verbose_name="IP address",
                help_text="Presented as string.",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="hostname",
            field=ralph.lib.mixins.fields.NullableCharField(
                default=None,
                max_length=255,
                blank=True,
                verbose_name="Hostname",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="is_gateway",
            field=models.BooleanField(default=False, verbose_name="Is gateway"),
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="is_management",
            field=models.BooleanField(
                default=False, verbose_name="Is management address"
            ),
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="is_public",
            field=models.BooleanField(
                editable=False, verbose_name="Is public", default=False
            ),
        ),
        migrations.AlterField(
            model_name="ipaddress",
            name="status",
            field=models.PositiveSmallIntegerField(
                default=1,
                choices=[(1, "used (fixed address in DHCP)"), (2, "reserved")],
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="dhcp_broadcast",
            field=models.BooleanField(
                default=True,
                db_index=True,
                verbose_name="Broadcast in DHCP configuration",
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="kind",
            field=models.ForeignKey(
                verbose_name="network kind",
                to="networks.NetworkKind",
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="network",
            name="max_ip",
            field=models.DecimalField(
                editable=False,
                decimal_places=0,
                max_digits=39,
                verbose_name="largest IP number",
                default=0,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="network",
            name="min_ip",
            field=models.DecimalField(
                editable=False,
                decimal_places=0,
                max_digits=39,
                verbose_name="smallest IP number",
                default=0,
            ),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="network",
            name="terminators",
        ),
        migrations.DeleteModel(
            name="NetworkTerminator",
        ),
        migrations.AddField(
            model_name="network",
            name="terminators",
            field=models.ManyToManyField(
                to="assets.BaseObject", verbose_name="network terminators", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="networkenvironment",
            name="domain",
            field=ralph.lib.mixins.fields.NullableCharField(
                null=True,
                max_length=255,
                blank=True,
                verbose_name="domain",
                help_text="Used in DHCP configuration.",
            ),
        ),
    ]
