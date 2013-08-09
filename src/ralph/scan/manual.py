# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import rq
import django_rq
from django.utils.importlib import import_module
from django.db import models as db

from ralph.discovery.models import IPAddress, Network, Device
from ralph.scan.errors import NoQueueError


def scan_address(address, plugins):
    """Queue manual discovery on the specified address."""

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
        result_ttl=3600,
    )
    return job


def _scan_address(address, plugins, **kwargs):
    """The function that is actually running on the worker."""

    job = rq.get_current_job()
    results = {}
    job.meta['messages'] = []
    job.meta['finished'] = []
    job.meta['status'] = {}
    for plugin_name in plugins:
        message = "Running plugin %s." % plugin_name
        job.meta['messages'].append((address, plugin_name, 'info', message))
        job.save()
        try:
            module = import_module(plugin_name)
        except ImportError as e:
            message = 'Failed to import: %s.' % e
            job.meta['messages'].append((address, plugin_name, 'error', message))
            job.meta['status'][plugin_name] = 'error'
        else:
            result = module.scan_address(address, **kwargs)
            results[plugin_name] = result
            for message in result.get('messages', []):
                job.meta['messages'].append((address, plugin_name, 'warning', message))
            job.meta['status'][plugin_name] = result.get('status', 'success')
        job.meta['finished'].append(plugin_name)
        job.save()
    return results




def find_devices(result):
    """Find all devices that can be possibly matched to this scan data."""

    ids = set(
        r['device']['id']
        for r in result.itervalues() if 'id' in r.get('device', {})
    )
    serials = set(
        r['device']['serial_number']
        for r in result.itervalues() if 'serial_number' in r.get('device', {})
    )
    macs = set()
    for r in result.itervalues():
        macs |= set(r.get('device', {}).get('mac_addresses', []))
    return Device.admin_objects.filter(
        db.Q(id__in=ids) |
        db.Q(sn__in=serials) |
        db.Q(ethernet__mac__in=macs)
    ).distinct()
