#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.django.common import nested_commit_on_success

from ralph.discovery.models import (Device, Ethernet, IPAddress)

SAVE_PRIORITY = 0


@nested_commit_on_success
def _merge_devs(dev, other_dev):
    for field, value in other_dev.__dict__.iteritems():
        if field.startswith('_'):
            continue
        if not getattr(dev, field):
            setattr(dev, field, value)
    dev.save(priority=SAVE_PRIORITY)
    for set_field in Device.__dict__.keys():
        if not set_field.endswith('_set'):
            continue
        if len(getattr(dev, set_field).all()):
            continue
        for child in getattr(other_dev, set_field).all():
            child.device = dev
            child.save(priority=SAVE_PRIORITY)
    other_dev.delete()


def _connect_macs(dev):
    macs = Ethernet.objects.filter(device=dev).values_list('mac')
    count = 0
    for mac, in macs:
        devs = Device.objects.filter(ethernet__mac=mac)
        for other_dev in devs:
            if other_dev == dev:
                continue
            _merge_devs(dev, other_dev)
            count += 1
    return count


def own_mac(ip, **kwargs):
    ip = str(ip)
    try:
        dev = IPAddress.objects.select_related().get(address=ip).device
    except IPAddress.DoesNotExist:
        return False, 'no device.', kwargs
    if dev is None:
        return False, 'no device.', kwargs
    count = _connect_macs(dev)
    return True, '%d own MACs connected.' % count, kwargs


def children_mac(ip, **kwargs):
    ip = str(ip)
    try:
        dev = IPAddress.objects.select_related().get(address=ip).device
    except IPAddress.DoesNotExist:
        return False, 'no device.', kwargs
    if dev is None:
        return False, 'no device.', kwargs
    count = 0
    child_count = 0
    for child_dev in dev.child_set.all():
        count += _connect_macs(child_dev)
        child_count += 1
    message = '%d MACs of %d children connected.' % (count, child_count)
    return True, message, kwargs
