# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import django_rq
from django.utils.importlib import import_module

from ralph.discovery.models import IPAddress, Network
from ralph.scan.errors import NoQueueError


def scan_address(address, plugins):
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
    ipaddress, created = IPAddress.objects.get_or_create(address=address)
    queue_name = network.queue.name
    queue = django_rq.get_queue(queue_name)
    job = queue.enqueue_call(
        func=_scan_address,
        args=(
            address,
            plugins,
        ),
        kwargs={
            'snmp_community': ipaddress.snmp_community,
#            'snmp_version': ipaddress.snmp_version,
            'snmp_version': '2c',
            'http_family': ipaddress.http_family,
            'snmp_name': ipaddress.snmp_name,
        },
        timeout=60,
        result_ttl=60,
    )
    return job

def _scan_address(address, plugins, **kwargs):
    results = []
    for plugin_name in plugins:
        module = import_module(plugin_name)
        result = module.scan_address(address, **kwargs)
        results.append(result)
    return results
