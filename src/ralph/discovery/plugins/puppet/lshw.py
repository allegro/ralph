#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import zlib

import jpath
from lck.django.common import nested_commit_on_success
from lck.django.common.models import MACAddressField

from ralph.discovery.models import DeviceType, Device,  EthernetSpeed, Memory,\
    Processor, ComponentModel, ComponentType, Storage, SERIAL_BLACKLIST,\
    DISK_VENDOR_BLACKLIST, DISK_PRODUCT_BLACKLIST, FibreChannel
from ralph.util import units, Eth, untangle
from ralph.discovery import hardware

from .facts import handle_facts_ethernets
from .util import assign_ips, get_logical_name


SAVE_PRIORITY = 53


@nested_commit_on_success
def parse_lshw(lshw, facts, is_virtual):
    try:
        lshw = zlib.decompress(lshw)
    except zlib.error:
        return False, "lshw decompression error."
    lshw, _ = hardware.lshw(as_string=lshw)
    prod_name = lshw['product']
    manufacturer = lshw['vendor'].replace(', Inc.', '')
    if prod_name.endswith(' ()'):
        prod_name = prod_name[:-3]
    if manufacturer and manufacturer in prod_name:
        model_name = prod_name
    else:
        model_name = "{} {}".format(manufacturer, prod_name)
    sn = facts.get('serialnumber') # use a Puppet fact because lshw gives
                                   # wrong serial numbers
    if sn in SERIAL_BLACKLIST:
        sn = None
    if is_virtual:
        model_type = DeviceType.virtual_server
    elif DeviceType.blade_server.matches(model_name):
        model_type = DeviceType.blade_server
    else:
        model_type = DeviceType.rack_server
    ethernets = list(handle_lshw_ethernets(lshw))
    ip_addresses, ethernets_facts = handle_facts_ethernets(facts)
    if not ethernets:
        return False, "Machine has no MAC addresses."
    dev = Device.create(sn=sn, model_name=model_name, model_type=model_type,
        ethernets=ethernets, priority=SAVE_PRIORITY)
    assign_ips(dev, ip_addresses)
    handle_lshw_memory(dev, lshw['bus']['memory'], is_virtual=is_virtual)
    handle_lshw_processors(dev, lshw['bus']['processor'], is_virtual=is_virtual)
    handle_lshw_storage(dev, lshw, is_virtual=is_virtual)
    handle_lshw_fibre_cards(dev, lshw, is_virtual=is_virtual)

    return dev, model_name

def handle_lshw_ethernets(lshw):
    ethernets = sorted((e for e in jpath.get_all('..network',
        lshw) if e), key=get_logical_name)
    for i, ethernet in enumerate(untangle(ethernets)):
        try:
            mac = MACAddressField.normalize(ethernet['serial'])
        except (ValueError, KeyError):
            continue
        if not mac:
            continue
        full_name = ethernet['product']
        if ethernet['vendor'] not in full_name:
            full_name = "{} {}".format(ethernet['vendor'], full_name)
        label = "{}: {}".format(get_logical_name(ethernet), full_name)
        caps = set(ethernet['capabilities'].keys())
        if '1000bt-fd' in caps or '1000bt' in caps:
            speed = EthernetSpeed.s1gbit.id
        elif '100bt-fd' in caps or '100bt' in caps:
            speed = EthernetSpeed.s100mbit.id
        else:
            speed = None
        yield Eth(label, mac, speed)

def handle_lshw_memory(dev, bus_memory, is_virtual=False):
    memory_banks = []
    for _mem in bus_memory:
        # we're interested only in the system memory, not in caches etc.
        if _mem['id'] == 'memory':
            memory_banks = _mem['memory']
            break
        elif _mem['id'].startswith('memory:'):
            memory_banks.extend(_mem['memory'])
    index = 0
    if isinstance(memory_banks, dict):
        memory_banks = [memory_banks]
    detected_memory = {}
    for memory in memory_banks:
        if 'size' not in memory:
            # empty slot
            continue
        index += 1
        size = int(memory['size']['value'] or 0)
        size /= units.size_divisor[memory['size']['units']]
        size = int(size)
        label = memory['slot']
        family = 'Virtual' if is_virtual else ''
        model, created = ComponentModel.concurrent_get_or_create(
            size=size, speed=0, type=ComponentType.memory.id,
            family=family, extra_hash='')
        if created:
            name = 'RAM %dMiB' % size
            if family:
                name = '%s %s' % (family, name)
            model.name = name
            model.save(priority=SAVE_PRIORITY)
        detected_memory[index] = label, model
    for mem in dev.memory_set.all():
        label, model = detected_memory.get(mem.index, (None, None))
        if mem.label != label or mem.model != model:
            mem.delete()
    for index, (label, model) in detected_memory.iteritems():
        mem, created = Memory.concurrent_get_or_create(device=dev, index=index)
        if created:
            mem.model = model
            mem.size = model.size
            mem.speed = model.speed
            mem.label = label
            mem.save(priority=SAVE_PRIORITY)

def handle_lshw_processors(dev, processors, is_virtual=False):
    if isinstance(processors, dict):
        processors = [processors]
    detected_cpus = {}
    for i, processor in enumerate(processors):
        if processor['disabled'] == 'true' or not processor['size']:
            continue
        label = 'CPU {}'.format(i + 1)
        speed = int(processor['size']['value'] or 0) # 'size', sic!
        speed /= units.speed_divisor[processor['size']['units']]
        speed = int(speed)
        family = processor['version'] or ''
        caps = processor['capabilities']
        extra = "\n".join([": ".join((key, ' '.join(e for e in
            untangle(caps[key]) if e) or '')) for key in sorted(caps.keys())])
        model, c = ComponentModel.concurrent_get_or_create(
            speed=speed, type=ComponentType.processor.id, extra=extra,
            extra_hash=hashlib.md5(extra).hexdigest(), family=family,
            cores=0)
        model.name = processor['product'] or 'CPU {} {}MHz'.format(family,
            speed)
        model.save(priority=SAVE_PRIORITY)
        detected_cpus[i+1] = label, model
    for cpu in dev.processor_set.all():
        label, model = detected_cpus.get(cpu.index, (None, None))
        if cpu.label != label or cpu.model != model:
            cpu.delete()
    for index, (label, model) in detected_cpus.iteritems():
        cpu, created = Processor.concurrent_get_or_create(
            device=dev, index=index)
        cpu.label = label
        cpu.model = model
        cpu.save(priority=SAVE_PRIORITY)

def handle_lshw_storage(dev, lshw, is_virtual=False):
    storages = []
    for storage in jpath.get_all('..disk', lshw):
        if not storage:
            continue
        if isinstance(storage, list):
            storages.extend(storage)
        else:
            storages.append(storage)
    storages.sort(key=get_logical_name)
    mount_points = set()
    for stor in storages:
        if 'logicalname' not in stor:
            continue
        ln = stor['logicalname']
        if isinstance(ln, list):
            mount_points.update(ln)
        else:
            mount_points.add(ln)
    dev.storage_set.filter(mount_point__in=mount_points).delete()
    for storage in storages:
        if 'size' in storage:
            size = storage['size']
        elif 'capacity' in storage:
            size = storage['capacity']
        else:
            # empty slot
            continue
        sn = unicode(storage.get('serial') or '') or None
        if not sn or sn.startswith('QM000') or \
                storage.get('vendor', '').strip().lower() in DISK_VENDOR_BLACKLIST or \
                storage.get('product', '').strip().lower() in DISK_PRODUCT_BLACKLIST:
            continue
        if sn:
            stor, created = Storage.concurrent_get_or_create(sn=sn, device=dev)
            stor.mount_point = storage.get('logicalname', None)
        else:
            stor, created = Storage.concurrent_get_or_create(sn=None, device=dev,
                mount_point=storage.get('logicalname', None))
        stor.size = int(size['value'])
        stor.size /= units.size_divisor[size['units']]
        stor.size = int(stor.size)
        stor.speed = 0
        if storage.get('vendor', '').strip():
            stor.label = storage['vendor'].strip() + ' '
        else:
            stor.label = ''
        if storage.get('product', '').strip():
            stor.label += storage['product'].strip()
        elif storage.get('description', '').strip():
            stor.label += storage['description'].strip()
        else:
            stor.label += 'Generic disk'
        caps = storage['capabilities']
        extra = "\n".join([": ".join((unicode(key), unicode(caps[key]) or '')) for key in
            sorted(caps.keys())])
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, speed=stor.speed, type=ComponentType.disk.id,
            family='', extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)

def handle_lshw_fibre_cards(dev, lshw, is_virtual=False):
    buses = []
    for bus in jpath.get_all('..bus', lshw):
        if not bus:
            continue
        if isinstance(bus, list):
            buses.extend(bus)
        else:
            buses.append(bus)
    buses = filter(lambda item: item['id'].startswith('fiber'), buses)
    buses.sort(key=lambda item: item['physid'])
    handled_buses = set()
    for bus in buses:
        physid = unicode(bus['physid'])
        for handled in handled_buses:
            if physid.startswith(handled):
                break
        else:
            fib, created = FibreChannel.concurrent_get_or_create(device=dev,
                physical_id=physid)
            fib.label = "{} {}".format(bus['vendor'], bus['product'])
            extra = fib.label
            fib.model, c = ComponentModel.concurrent_get_or_create(
                type=ComponentType.fibre.id, family=bus['vendor'],
                            extra_hash=hashlib.md5(extra).hexdigest(),
                            extra=extra)
            fib.model.name = bus['product']
            fib.model.save(priority=SAVE_PRIORITY)
            fib.save(priority=SAVE_PRIORITY)
        handled_buses.add(physid)
