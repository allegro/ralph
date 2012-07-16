#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.discovery.models import (Device, DeviceType, DeviceModel, IPAddress, Network)

def _make_dc_rack(dc_no, rack_no):
    if dc_no is None:
        return None, None
    dev_model, created = DeviceModel.concurrent_get_or_create(
            name='Data center', type=DeviceType.data_center.id)
    dc, created = Device.concurrent_get_or_create(sn=dc_no,
                                                   model=dev_model)
    if created:
        dc.name = dc_no
    dc.save(update_last_seen=True)

    if rack_no is None:
        rack = None
    else:
        rack_name = 'Rack %s' % rack_no
        dev_model, created = DeviceModel.concurrent_get_or_create(
                name='Rack', type=DeviceType.rack.id)
        rack, created = Device.concurrent_get_or_create(
                sn=rack_name, model=dev_model)
        if created:
            rack.name = rack_name
        rack.parent = dc
        rack.save(update_last_seen=True)
    return dc, rack

def _connect_dc(ip, dev):
    try:
        network = Network.from_ip(ip)
        dc_no = network.data_center.name if network.data_center else None
        if network.rack:
            rack_no = network.rack
            if ',' in rack_no:
                rack_no = rack_no.split(',', 1)[0].strip()
        else:
            rack_no = None
    except IndexError:
        dc_no = None
        rack_no = None
    dc, rack = _make_dc_rack(dc_no, rack_no)
    if rack:
        dev.parent = rack
    elif dev.parent == None:
        dev.parent = rack or dc
    else:
        return 'Already has better info.'

    stack = [dev]
    while stack:
        dev = stack.pop()
        for child in dev.child_set.all():
            stack.append(child)
        if rack:
            dev.rack = rack.name
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
