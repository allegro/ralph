# -*- coding: utf-8 -*-

"""
Set of usefull functions to retrieve data from LSHW.
"""

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

from ralph.discovery.models import (
    DISK_PRODUCT_BLACKLIST,
    DISK_VENDOR_BLACKLIST,
    DeviceType,
)
from ralph.scan.errors import Error
from ralph.util import units, untangle


TAG_TRANSLATION_PAIRS = set([
    ('node', 'class'),
    ('capability', 'id'),
    ('setting', 'id'),
    ('resource', 'type'),
])
TEXT_TRANSLATION_PAIRS = set([
    ('setting', 'value'),
])
FC_CARD_PHYSICAL_ID_EXPRESSION = re.compile(r"([1-9][0-9]*)")


def _nullify(value):
    if value is not None:
        raise ValueError
    return Null


def _get_logical_name(arg):
    l_name = arg['logicalname']
    if isinstance(l_name, list):
        return l_name[0]
    else:
        return l_name


def parse_lshw(raw_data):
    parser = ET.ETCompatXMLParser(recover=True)
    response = ET.fromstring(raw_data, parser=parser)
    if response.tag is None or response.tag.upper() != 'NODE':
        raise Error('Lshw parse error.')
    for element in response.findall('.//'):
        for k in element.attrib.keys():
            try:
                v = element.attrib[k]
            except UnicodeDecodeError:
                continue   # value has bytes not possible to decode with UTF-8
            if (element.tag, k) in TAG_TRANSLATION_PAIRS:
                try:
                    element.tag = v
                except ValueError:
                    pass
                continue
            if (element.tag, k) in TEXT_TRANSLATION_PAIRS:
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
        etree_to_dict(
            response,
            _converters=[
                _nullify,
                int,
                float,
                lck.xml.converters._datetime,
                lck.xml.converters._datetime_strip_tz,
            ],
        ),
    )[1]


def handle_lshw(data, is_virtual):
    lshw = parse_lshw(data)
    results = {}
    prod_name = lshw['product']
    manufacturer = lshw['vendor'].replace(', Inc.', '')
    if prod_name.endswith(' ()'):
        prod_name = prod_name[:-3]
    if manufacturer and manufacturer in prod_name:
        model_name = prod_name
    else:
        model_name = "{} {}".format(manufacturer, prod_name)
    results['model_name'] = model_name
    if is_virtual:
        model_type = DeviceType.virtual_server
    elif DeviceType.blade_server.matches(model_name):
        model_type = DeviceType.blade_server
    else:
        model_type = DeviceType.rack_server
    results['type'] = model_type.raw
    mac_addresses = handle_lshw_mac_addresses(lshw)
    if mac_addresses:
        results['mac_addresses'] = mac_addresses
    memory = handle_lshw_memory(lshw['bus']['memory'], is_virtual)
    if memory:
        results['memory'] = memory
    processors = handle_lshw_processors(lshw['bus']['processor'], is_virtual)
    if processors:
        results['processors'] = processors
    disks = handle_lshw_storage(lshw)
    if disks:
        results['disks'] = disks
    fc_cards = handle_lshw_fibrechannel_cards(lshw)
    if fc_cards:
        results['fibrechannel_cards'] = fc_cards
    return results


def handle_lshw_mac_addresses(lshw):
    mac_addresses = set()
    ethernets = sorted(
        (e for e in jpath.get_all('..network', lshw) if e),
        key=_get_logical_name,
    )
    for i, ethernet in enumerate(untangle(ethernets)):
        try:
            mac = MACAddressField.normalize(ethernet['serial'])
        except (ValueError, KeyError):
            continue
        if not mac:
            continue
        mac_addresses.add(mac)
    return list(mac_addresses)


def handle_lshw_memory(bus_memory, is_virtual=False):
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
    detected_memory = []
    for memory in memory_banks:
        if 'size' not in memory:
            # empty slot
            continue
        index += 1
        size = int(memory['size']['value'] or 0)
        size /= units.size_divisor[memory['size']['units']]
        size = int(size)
        label = memory['slot']
        if is_virtual:
            label = 'Virtual %s' % label
        detected_memory.append({
            'label': label,
            'size': size,
            'index': index,
        })
    return detected_memory


def handle_lshw_processors(bus_processors, is_virtual=False):
    if isinstance(bus_processors, dict):
        bus_processors = [bus_processors]
    detected_cpus = []
    family = None
    for processor in bus_processors:
        family = processor['version'] or (
            'Virtual CPU' if is_virtual else processor['product']
        )
        if family:
            break
    for i, processor in enumerate(bus_processors):
        if processor['disabled'] == 'true' or not processor['size']:
            continue
        label = 'CPU {}'.format(i + 1)
        speed = int(processor['size']['value'] or 0)
        speed /= units.speed_divisor[processor['size']['units']]
        speed = int(speed)
        detected_cpus.append({
            'index': i + 1,
            'label': label,
            'speed': speed,
            'family': family,
            'model_name': processor['product'] or 'CPU {} {}MHz'.format(
                family, speed,
            )
        })
    return detected_cpus


def handle_lshw_storage(lshw):
    storages = []
    for storage in jpath.get_all('..disk', lshw):
        if not storage:
            continue
        if isinstance(storage, list):
            storages.extend(storage)
        else:
            storages.append(storage)
    detected_storages = []
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
        if (
            not sn or
            sn.startswith('QM000') or
            storage.get(
                'vendor', '',
            ).strip().lower() in DISK_VENDOR_BLACKLIST or
            storage.get(
                'product', '',
            ).strip().lower() in DISK_PRODUCT_BLACKLIST
        ):
            continue
        mount_point = storage.get('logicalname', None)
        storage_size = int(size['value'])
        storage_size /= units.size_divisor[size['units']]
        storage_size = int(storage_size)
        label = ''
        if storage.get('vendor', '').strip():
            label = storage['vendor'].strip() + ' '
        if storage.get('product', '').strip():
            label += storage['product'].strip()
        elif storage.get('description', '').strip():
            label += storage['description'].strip()
        else:
            label += 'Generic disk'
        family = storage['vendor'].strip() or 'Generic disk'
        detected_storages.append({
            'mount_point': mount_point,
            'serial_number': sn,
            'size': storage_size,
            'label': label,
            'family': family,
        })
    return detected_storages


def handle_lshw_fibrechannel_cards(lshw):
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
    fc_cards = []
    for bus in buses:
        handle = unicode(bus['handle'])
        m = FC_CARD_PHYSICAL_ID_EXPRESSION.search(handle)
        if not m:
            continue
        physid = m.group(1)
        if physid in handled_buses:
            continue
        handled_buses.add(physid)
        fc_cards.append({
            'physical_id': physid,
            'label': "{} {}".format(bus['vendor'], bus['product']),
            'model_name': bus['product'],
        })
    return fc_cards
