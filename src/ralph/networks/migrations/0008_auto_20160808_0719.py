# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ipaddress
from itertools import chain

from django.db import migrations, models

IPADDRESS_STATUS_RESERVED = 2


def _reserve_margin_addresses(network, bottom_count, top_count, IPAddress):
    ips = []
    ips_query = IPAddress.objects.filter(
        models.Q(
            number__gte=network.min_ip + 1,
            number__lte=network.min_ip + bottom_count + 1,
        )
        | models.Q(number__gte=network.max_ip - top_count, number__lte=network.max_ip)
    )
    existing_ips = set(ips_query.values_list("number", flat=True))
    to_create = set(
        chain.from_iterable(
            [
                range(int(network.min_ip + 1), int(network.min_ip + bottom_count + 1)),  # noqa
                range(int(network.max_ip - top_count), int(network.max_ip)),
            ]
        )
    )
    to_create = to_create - existing_ips
    for ip_as_int in to_create:
        ips.append(
            IPAddress(
                address=str(ipaddress.ip_address(ip_as_int)),
                number=ip_as_int,
                network=network,
                status=IPADDRESS_STATUS_RESERVED,
            )
        )
    print("Creating {} ips for {}".format(len(ips), network))
    IPAddress.objects.bulk_create(ips)
    ips_query.update(status=IPADDRESS_STATUS_RESERVED)


def create_reserved_ips(apps, schema_editor):
    IPAddress = apps.get_model("networks", "IPAddress")
    Network = apps.get_model("networks", "Network")

    for network in Network.objects.all():
        _reserve_margin_addresses(
            network,
            network.reserved_from_beginning,
            network.reserved_from_end,
            IPAddress,
        )


def remove_reserved_ips(apps, schema_editor):
    IPAddress = apps.get_model("networks", "IPAddress")
    ips = IPAddress.objects.filter(
        models.Q(ethernet__isnull=True)
        | (
            models.Q(ethernet__base_object__isnull=True)
            & models.Q(ethernet__mac__isnull=False)
        ),
        status=IPADDRESS_STATUS_RESERVED,
        gateway_network__isnull=True,
    )
    print("Removing {} reserved IPs".format(ips.count()))
    ips.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0007_auto_20160804_1409"),
    ]

    operations = [
        migrations.AddField(
            model_name="network",
            name="reserved_from_beginning",
            field=models.PositiveIntegerField(
                help_text="Number of addresses to be omitted in DHCP automatic assignmentcounted from the first IP in range (excluding network address)",
                default=10,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="reserved_from_end",
            field=models.PositiveIntegerField(
                help_text="Number of addresses to be omitted in DHCP automatic assignmentcounted from the last IP in range (excluding broadcast address)",
                default=0,
            ),
        ),
        migrations.RunPython(remove_reserved_ips, reverse_code=create_reserved_ips),
    ]
