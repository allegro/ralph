# -*- coding: utf-8 -*-

"""
Pre-scan all IP addresses from specified networks or environments. This scan
checks that IP address is available. It also sets some additional data,
like a SNMP name, SNMP community and SNMP version.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
import itertools
import datetime

import django_rq

from django.conf import settings

from ralph.util.network import ping
from ralph.discovery.http import get_http_family
from ralph.discovery.models import IPAddress, Network
from ralph.scan.snmp import get_snmp
from ralph.scan.errors import NoQueueError


ADDRESS_GROUP_SIZE = 24


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


def queue_autoscan_environment(environment):
    """Queues a pre-scan of all scannable networks in the environment."""

    if not environment.queue:
        raise NoQueueError(
            "No discovery queue defined for environment {0}.".format(
                environment,
            ),
        )
    ip_numbers = set()
    for network in environment.network_set.all().order_by(
        '-min_ip', 'max_ip',
    ):
        ip_numbers |= set(range(network.min_ip, network.max_ip + 1))
        network.last_scan = datetime.datetime.now()
        network.save()
    range_start = 0
    for ip_number in sorted(ip_numbers):
        if range_start == 0:
            range_start = ip_number
        if ip_number + 1 in ip_numbers:
            continue
        queue_autoscan_ip_addresses_range(
            range_start,
            ip_number,
            queue_name=environment.queue.name
        )
        range_start = 0


def queue_autoscan_network(network, queue_name=None):
    """Queues a pre-scan of a whole network on the right worker."""

    if not queue_name:
        if not network.environment or not network.environment.queue:
            raise NoQueueError(
                "No discovery queue defined for network "
                "environment {0}.".format(network),
            )
        queue_name = network.environment.queue.name
    queue = django_rq.get_queue(queue_name)
    for group in _split_into_groups(
        network.network.iterhosts(),
        ADDRESS_GROUP_SIZE,
    ):
        queue.enqueue_call(
            func=_autoscan_group,
            args=(group,),
            timeout=90,
            result_ttl=0,
        )
    network.last_scan = datetime.datetime.now()
    network.save()


def queue_autoscan_ip_addresses_range(min_ip_number, max_ip_number, queue_name):  # noqa
    ip_addresses = [
        ipaddr.IPAddress(ip_number)
        for ip_number in xrange(min_ip_number, max_ip_number + 1)
    ]
    queue = django_rq.get_queue(queue_name)
    for group in _split_into_groups(
        ip_addresses,
        ADDRESS_GROUP_SIZE,
    ):
        queue.enqueue_call(
            func=_autoscan_group,
            args=(group,),
            timeout=90,
            result_ttl=0,
        )


def queue_autoscan_address(address):
    """Queues an autoscan of a single address on the right worker."""

    try:
        network = Network.from_ip(address)
    except IndexError:
        raise NoQueueError(
            "Address {0} doesn't belong to any configured "
            "network.".format(address),
        )
    if not network.environment or not network.environment.queue:
        raise NoQueueError(
            "The network environment {0} has no discovery queue.".format(
                network,
            ),
        )
    queue_name = network.environment.queue.name
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
        autoscan_address(address)


def autoscan_address(address):
    """Autoscans a single address on the worker."""

    try:
        ipaddress = IPAddress.objects.get(address=unicode(address))
    except IPAddress.DoesNotExist:
        ipaddress = None
    if ipaddress and ipaddress.is_buried:
        return
    pinged = ping(address)
    if pinged:
        if not ipaddress:
            ipaddress, created = IPAddress.objects.get_or_create(
                address=unicode(address),
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
            ipaddress.dead_ping_count += 1
            if ipaddress.dead_ping_count >= settings.DEAD_PING_COUNT:
                # remove previous values only if this IP address already died
                ipaddress.http_family = None
                ipaddress.snmp_name = None
                ipaddress.snmp_community = None
                ipaddress.snmp_version = None
            ipaddress.save(update_last_seen=False)
