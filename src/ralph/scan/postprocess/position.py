# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import (
    Device,
    DeviceModel,
    DeviceType,
    Network,
)


def _make_dc(dc_no):
    if dc_no is None:
        return
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


def _connect_dc(ip_address, device):
    try:
        network = Network.from_ip(ip_address)
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
        device.parent = rack
    elif device.parent is None:
        device.parent = rack or dc
    else:
        return  # Already has better info...
    stack = [device]
    while stack:
        device = stack.pop()
        for child in device.child_set.all():
            stack.append(child)
        if rack:
            device.rack = rack.sn if rack.sn else None
        if dc_no:
            device.dc = dc_no
        device.save()


def run_job(ip, **kwargs):
    device = ip.device
    if not device:
        return  # no device...
    if device.parent and (
        device.parent.model is None or
        device.parent.model.type not in (
            DeviceType.data_center,
            DeviceType.rack,
        )
    ):
        return  # has parent...
    _connect_dc(ip.address, device)
