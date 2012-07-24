#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssl
import hashlib

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import plugin, Eth
from ralph.discovery import hp_ilo
from ralph.discovery.models import (Device, Processor, Memory,
        IPAddress, ComponentModel, ComponentType, DeviceType)


ILO_USER, ILO_PASSWORD = settings.ILO_USER, settings.ILO_PASSWORD
SAVE_PRIORITY = 0


def make_device(ilo, ip):
    if ilo.model.startswith('HP ProLiant BL'):
        t = DeviceType.blade_server
    else:
        t = DeviceType.rack_server
    ethernets = [Eth(label, mac, speed=None) for label, mac in ilo.ethernets]
    dev = Device.create(
            ethernets=ethernets,
            model_name=ilo.model,
            model_type=t,
            sn=ilo.sn,
            name=ilo.name,
            mgmt_firmware=ilo.firmware,
            raw=ilo.raw,
        )
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)

    ipaddr, created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save()

    if dev.parent and dev.parent.management:
        dev.management = dev.parent.management
    else:
        dev.management = ipaddr
    dev.save(priority=SAVE_PRIORITY)

    return dev

def make_components(ilo, dev):
    for i, (label, size, speed) in enumerate(ilo.memories):
        mem, created = Memory.concurrent_get_or_create(device=dev, index=i + 1)
        mem.size = size
        mem.speed = speed
        mem.label = label
        mem.model, c = ComponentModel.concurrent_get_or_create(
            size=mem.size, speed=mem.speed, type=ComponentType.memory.id,
            family='', extra_hash='')
        if c:
            mem.model.name = 'RAM %dMiB, %dMHz' % (mem.size, mem.speed)
            mem.model.save()
        mem.save()

    for i, (label, speed, cores, extra, family) in enumerate(ilo.cpus):
        cpu, created = Processor.concurrent_get_or_create(device=dev,
                                                          index=i + 1)
        family = family or ''
        cpu.label = label
        cpu.model, c = ComponentModel.concurrent_get_or_create(
            speed=speed, type=ComponentType.processor.id, extra=extra,
            extra_hash=hashlib.md5(extra).hexdigest(), cores=cores,
            family=family)
        if c:
            cpu.model.name = 'CPU %s %dMHz, %s-core' % (family, speed, cores)
            cpu.model.save()
        cpu.save()

@nested_commit_on_success
def _run_ilo(ip):
    ilo = hp_ilo.IloHost(ip, ILO_USER, ILO_PASSWORD)
    ilo.update()
    dev = make_device(ilo, ip)
    make_components(ilo, dev)
    return dev.name

@plugin.register(chain='discovery', requires=['ping', 'http'])
def ilo_hp(**kwargs):
    if not ILO_USER or not ILO_PASSWORD:
        return False, "not configured", kwargs
    if kwargs.get('http_family', '') not in ('Unspecified', 'RomPager', 'HP'):
        return False, 'no match.', kwargs
    ip = str(kwargs['ip'])
    try:
        name = _run_ilo(ip)
    except (hp_ilo.Error, ssl.SSLError) as e:
        return False, str(e), kwargs
    return True, name, kwargs

