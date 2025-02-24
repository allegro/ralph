# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


def move_m2m_to_dns_server_group(apps, schema_editor):
    Network = apps.get_model("networks", "Network")
    DNSServer = apps.get_model("dhcp", "DNSServer")
    DNSServerGroup = apps.get_model("dhcp", "DNSServerGroup")
    DNSServerGroupOrder = apps.get_model("dhcp", "DNSServerGroupOrder")
    created_dns_servers_group_counter = 1
    dns_group_list = []
    for network in Network.objects.all():
        if not network.dns_servers.count():
            continue
        dns_group_list.append(
            tuple(network.dns_servers.values_list("id", flat=True).order_by("id"))
        )

    dns_servers_to_dns_group_mapper = {}
    for dns_servers in set(dns_group_list):
        dns_server_group = DNSServerGroup.objects.create(
            name="DNS server group #{}".format(created_dns_servers_group_counter)
        )
        created_dns_servers_group_counter += 1
        for idx, server_id in enumerate(dns_servers):
            DNSServerGroupOrder.objects.create(
                dns_server_group=dns_server_group,
                dns_server=DNSServer.objects.get(id=server_id),
                order=idx * 10,
            )
        dns_servers_to_dns_group_mapper[dns_servers] = dns_server_group

    for network in Network.objects.all():
        key = tuple(network.dns_servers.values_list("id", flat=True).order_by("id"))
        if not key:
            continue
        dns_server_group = dns_servers_to_dns_group_mapper[key]
        network.dns_servers_group = dns_server_group
        network.save(update_fields=["dns_servers_group"])


def move_dns_server_group_to_m2m(apps, schema_editor):
    Network = apps.get_model("networks", "Network")
    for network in Network.objects.filter(dns_servers_group__isnull=False):
        dns_servers = network.dns_servers_group.servers.all()
        network.dns_servers.add(*dns_servers)


class Migration(migrations.Migration):
    dependencies = [
        ("dhcp", "0005_change_related_name"),
        ("networks", "0010_auto_20170216_1230"),
    ]

    operations = [
        migrations.AddField(
            model_name="network",
            name="dns_servers_group",
            field=models.ForeignKey(
                to="dhcp.DNSServerGroup",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.RunPython(
            move_m2m_to_dns_server_group, reverse_code=move_dns_server_group_to_m2m
        ),
    ]
