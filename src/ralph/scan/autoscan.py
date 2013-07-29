# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools
import datetime

import django_rq

from ralph.util.network import ping
from ralph.discovery.http import get_http_family
from ralph.discovery.models import IPAddress, Network
from ralph.scan.snmp import get_snmp
from ralph.scan.errors import NoQueueError


ADDRESS_GROUP_SIZE = 32


def _split_into_groups(iterable, group_size):
    """
    >>> list(_split_into_groups(range(10), 2))
    [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]
    >>> list(_split_into_groups(range(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """
    for g, group in itertools.groupby(
            enumerate(iterable),
            lambda items: items[0] // group_size
        ):
        yield [item for (i, item) in group]


def autoscan_data_center(data_center):
    """Queues a scan of all scannable networks in the data center."""

    for network in data_center.network_set.exclude(queue=None):
        autoscan_network(network)


def autoscan_network(network):
    """Queues a scan of a whole network on the right worker."""

    if not network.queue:
        raise NoQueueError(
            "No discovery queue defined for network {0}.".format(network),
        )
    queue_name = network.queue.name
    queue = django_rq.get_queue(queue_name)
    for group in _split_into_groups(
            network.network.iterhosts(),
            ADDRESS_GROUP_SIZE,
        ):
        queue.enqueue_call(
            func=_autoscan_group,
            args=(group,),
            timeout=60,
            result_ttl=0,
        )
    network.last_scan = datetime.datetime.now()
    network.save()


def autoscan_address(address):
    """Queues a scan of a single address on the right worker."""

    try:
        network = Network.from_ip(address)
    except IndexError:
        raise NoQueueError(
            "Address {0} doesn't belong to any configured "
            "network.".format(address),
        )
    if not network.queue:
        raise NoQueueError(
            "The network {0} has no discovery queue.".format(network),
        )
    queue_name = network.queue.name
    queue = django_rq.get_queue(queue_name)
    queue.enqueue_call(
        func=_autoscan_group,
        args=([address],),
        timeout=60,
        result_ttl=0,
    )


def _autoscan_group(addresses):
    """This is the function that actually gets queued during autoscanning."""

    for address in addresses:
        _autoscan_address(address)


def _autoscan_address(address):
    """Autoscans a single address on the worker."""

    try:
        ipaddress = IPAddress.objects.get(address=address)
    except IPAddress.DoesNotExist:
        ipaddress = None
    if ipaddress and ipaddress.is_buried:
        return
    pinged = ping(address)
    if pinged:
        if not ipaddress:
            ipaddress, created = IPAddress.objects.get_or_create(
                address=address,
            )
        ipaddress.http_family = get_http_family(ipaddress.address)
        (
            ipaddress.snmp_name,
            ipaddress.snmp_community,
            ipaddress.snmp_version,
        ) = get_snmp(ipaddress)
        ipaddress.dead_ping_count = 0
        ipaddress.save(update_last_seen=True)
    else:
        if ipaddress:
            ipaddress.http_family = None
            ipaddress.snmp_name = None
            ipaddress.snmp_community = None
            ipaddress.snmp_version = None
            ipaddress.dead_ping_count += 1
            ipaddress.save(update_last_seen=False)
