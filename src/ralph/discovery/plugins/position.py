#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.discovery.models import (
    Device,
    DeviceModel,
    DeviceType,
    IPAddress,
    Network,
)


def _make_dc(dc_no):
    if dc_no is None:
        return None
    dev_model, created = DeviceModel.concurrent_get_or_create(
        name='Data center',
        defaults={
            'type': DeviceType.data_center.id,
        },
    )
    dc, created = Device.concurrent_get_or_create(
        sn=dc_no,
        defaults={
            'model': dev_model,
        },
    )
    if created:
        dc.name = dc_no
    dc.save(update_last_seen=True)
    return dc


def _connect_dc(ip, dev):
    try:
        network = Network.from_ip(ip)
    except IndexError:
        dc_no = None
        rack = None
    else:
        dc_no = network.data_center.name if network.data_center else None
        rack = None
        for rack in network.racks.all()[:1]:
            break

    dc = _make_dc(dc_no)
    if rack:
        dev.parent = rack
    elif dev.parent is None:
        dev.parent = rack or dc
    else:
        return 'Already has better info.'

    stack = [dev]
    while stack:
        dev = stack.pop()
        for child in dev.child_set.all():
            stack.append(child)
        if rack:
            dev.rack = rack.sn if rack.sn else None
        if dc_no:
            dev.dc = dc_no
        dev.save()
    return '%s %s' % (dc_no, rack.name if rack else '?')


@plugin.register(chain='postprocess', requires=['ping'])
def position(ip, **kwargs):
    ip = str(ip)
    try:
        ipaddr = IPAddress.objects.select_related().get(address=ip)
    except IPAddress.DoesNotExist:
        return False, 'no device.', kwargs
    dev = ipaddr.device
    if dev is None:
        return False, 'no device.', kwargs
    if dev.parent and (
            dev.parent.model is None or
            dev.parent.model.type not in (
                DeviceType.data_center.id,
                DeviceType.rack.id,
            )
    ):
        return False, 'has parent.', kwargs
    name = _connect_dc(ip, dev)
    return True, name, kwargs
