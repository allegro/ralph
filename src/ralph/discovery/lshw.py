#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

import jpath
from lck.django.common.models import MACAddressField
from lck.lang import Null, nullify
from lck.xml import etree_to_dict
import lck.xml.converters
from lxml import etree as ET

from ralph.util import units, Eth, untangle
from ralph.discovery.models import (EthernetSpeed, Memory, Processor,
                                    ComponentModel, ComponentType, Storage,
                                    DISK_VENDOR_BLACKLIST,
                                    DISK_PRODUCT_BLACKLIST, FibreChannel,
                                    DeviceType, Device)


class Error(Exception):
    pass


class EthernetsError(Error):
    pass


def get_logical_name(arg):
    l_name = arg['logicalname']
    if isinstance(l_name, list):
        return l_name[0]
    else:
        return l_name

_tag_translation_pairs = set([
    ('node', 'class'), ('capability', 'id'), ('setting', 'id'),
    ('resource', 'type'),
])

_text_translation_pairs = set([
    ('setting', 'value'),
])


def _nullify(value):
    if value is not None:
        raise ValueError
    return Null


def parse_lshw(as_string):
    parser = ET.ETCompatXMLParser(recover=True)
    response = ET.fromstring(as_string, parser=parser)
    if response.tag is None or response.tag.upper() != 'NODE':
        return None, as_string
    for element in response.findall('.//'):
        for k in element.attrib.keys():
            try:
                v = element.attrib[k]
            except UnicodeDecodeError:
                continue   # value has bytes not possible to decode with UTF-8
            if (element.tag, k) in _tag_translation_pairs:
                try:
                    element.tag = v
                except ValueError:
                    pass
                continue
            if (element.tag, k) in _text_translation_pairs:
                element.text = v
                continue
            if k == 'units':
                value = ET.Element(b'value')
                value.text = element.text
                element.text = ''
                element.append(value)
            child = ET.Element(k)
            child.text = v
            element.append(child)
    return nullify(
        etree_to_dict(response, _converters=[
            _nullify,
            int,
            float,
            lck.xml.converters._datetime,
            lck.xml.converters._datetime_strip_tz,
        ]))[1]


def handle_lshw(data, is_virtual=False, sn=None, priority=0):
    lshw = parse_lshw(as_string=data)
    prod_name = lshw['product']
    manufacturer = lshw['vendor'].replace(', Inc.', '')
    if prod_name.endswith(' ()'):
        prod_name = prod_name[:-3]
    if manufacturer and manufacturer in prod_name:
        model_name = prod_name
    else:
        model_name = "{} {}".format(manufacturer, prod_name)
    if is_virtual:
        model_type = DeviceType.virtual_server
    elif DeviceType.blade_server.matches(model_name):
        model_type = DeviceType.blade_server
    else:
        model_type = DeviceType.rack_server
    ethernets = list(handle_lshw_ethernets(lshw))
    if not ethernets:
        raise EthernetsError("Machine has no MAC addresses.")
    dev = Device.create(sn=sn, model_name=model_name, model_type=model_type,
                        ethernets=ethernets, priority=priority)
    handle_lshw_memory(dev, lshw['bus']['memory'], is_virtual=is_virtual)
    handle_lshw_processors(dev, lshw['bus']['processor'],
                           is_virtual=is_virtual)
    handle_lshw_storage(dev, lshw, is_virtual=is_virtual)
    handle_lshw_fibre_cards(dev, lshw, is_virtual=is_virtual)
    return dev


def handle_lshw_ethernets(lshw):
    ethernets = sorted(
        (e for e in jpath.get_all('..network', lshw) if e),
        key=get_logical_name)
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


def handle_lshw_memory(dev, bus_memory, is_virtual=False, priority=0):
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
        model, created = ComponentModel.create(
            ComponentType.memory,
            family=family,
            size=size,
            priority=priority,
        )
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
            mem.save(priority=priority)


def handle_lshw_processors(dev, processors, is_virtual=False, priority=0):
    if isinstance(processors, dict):
        processors = [processors]
    detected_cpus = {}
    family = None
    for processor in processors:
        family = processor['version'] or (
            'Virtual CPU' if is_virtual else processor['product']
        )
        if family:
            break
    if not family:
        return   # skip CPU changes if we cannot determine family
    for i, processor in enumerate(processors):
        if processor['disabled'] == 'true' or not processor['size']:
            continue
        label = 'CPU {}'.format(i + 1)
        speed = int(processor['size']['value'] or 0)   # 'size', sic!
        speed /= units.speed_divisor[processor['size']['units']]
        speed = int(speed)
        model, c = ComponentModel.create(
            ComponentType.processor,
            speed=speed,
            family=family,
            name=processor['product'] or 'CPU {} {}MHz'.format(family, speed),
            priority=priority
        )
        detected_cpus[i + 1] = label, model
    for cpu in dev.processor_set.all():
        label, model = detected_cpus.get(cpu.index, (None, None))
        if cpu.label != label or cpu.model != model:
            cpu.delete()
    for index, (label, model) in detected_cpus.iteritems():
        cpu, created = Processor.concurrent_get_or_create(
            device=dev, index=index)
        cpu.label = label
        cpu.model = model
        cpu.save(priority=priority)


def get_storage_from_lshw(lshw, no_ignore=False):
    storages = []
    for storage in jpath.get_all('..disk', lshw):
        if not storage:
            continue
        if isinstance(storage, list):
            storages.extend(storage)
        else:
            storages.append(storage)
    mount_points = set()
    for storage in storages:
        if 'logicalname' not in storage:
            continue
        ln = storage['logicalname']
        if isinstance(ln, list):
            mount_points.update(ln)
        else:
            mount_points.add(ln)
    parsed_storages = []
    for storage in storages:
        if 'size' in storage:
            size = storage['size']
        elif 'capacity' in storage:
            size = storage['capacity']
        else:
            # empty slot
            continue
        sn = unicode(storage.get('serial') or '') or None
        if sn and sn.startswith('OCZ-'):
            sn = sn.replace('OCZ-', '')
        if (not sn or (sn.startswith('QM000') and not no_ignore) or
            (storage.get('vendor', '').strip().lower() in
                DISK_VENDOR_BLACKLIST) or
            (storage.get('product', '').strip().lower() in
                DISK_PRODUCT_BLACKLIST)):
            continue
        mount_point = storage.get('logicalname', None)
        storage_size = int(size['value'])
        storage_size /= units.size_divisor[size['units']]
        storage_size = int(storage_size)
        storage_speed = 0
        label = ''
        if storage.get('vendor', '').strip():
            label = storage['vendor'].strip() + ' '
        if storage.get('product', '').strip():
            label += storage['product'].strip()
        elif storage.get('description', '').strip():
            label += storage['description'].strip()
        else:
            label += 'Generic disk'
        parsed_storages.append({
            'mount_point': mount_point,
            'sn': sn,
            'size': storage_size,
            'speed': storage_speed,
            'label': label,
        })
    return mount_points, parsed_storages


def handle_lshw_storage(dev, lshw, is_virtual=False, priority=0):
    mount_points, storages = get_storage_from_lshw(lshw)
    dev.storage_set.filter(mount_point__in=mount_points).delete()
    for storage in storages:
        sn = storage['sn'] if storage['sn'] else None
        stor, created = Storage.concurrent_get_or_create(
            sn=sn,
            mount_point=storage['mount_point'],
            device=dev,
        )
        stor.size = storage['size']
        stor.speed = storage['speed']
        stor.label = storage['label']
        stor.model, c = ComponentModel.create(
            ComponentType.disk,
            size=stor.size,
            speed=stor.speed,
            family=stor.label,
            priority=priority,
        )
        stor.save(priority=priority)


def handle_lshw_fibre_cards(dev, lshw, is_virtual=False, priority=0):
    buses = []
    for bus in jpath.get_all('..bus', lshw):
        if not bus:
            continue
        if isinstance(bus, list):
            buses.extend(bus)
        else:
            buses.append(bus)
    buses = filter(lambda item: item['id'].startswith('fiber'), buses)
    buses.sort(key=lambda item: item['handle'])
    handled_buses = set()
    detected_fc_cards = set()
    for bus in buses:
        handle = unicode(bus['handle'])
        m = re.search(r"([1-9][0-9]*)", handle)
        if not m:
            continue
        physid = m.group(1)
        if physid in handled_buses:
            continue
        fib, created = FibreChannel.concurrent_get_or_create(
            device=dev, physical_id=physid)
        fib.label = "{} {}".format(bus['vendor'], bus['product'])
        fib.model, c = ComponentModel.create(
            ComponentType.fibre,
            family=bus['vendor'],
            name=bus['product'],
            priority=priority,
        )
        fib.save(priority=priority)
        handled_buses.add(physid)
        detected_fc_cards.add(fib.pk)
    dev.fibrechannel_set.exclude(pk__in=detected_fc_cards).delete()
