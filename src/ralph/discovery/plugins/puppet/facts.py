#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import re
import zlib

from lck.django.common import nested_commit_on_success

from ralph.util import network, units, Eth
from ralph.discovery import hardware
from ralph.discovery.models import (DeviceType, Device, Memory, Processor,
    ComponentModel, ComponentType, Storage, SERIAL_BLACKLIST,
    DISK_VENDOR_BLACKLIST, DISK_PRODUCT_BLACKLIST)

from .util import assign_ips, get_default_mac


SAVE_PRIORITY = 52


@nested_commit_on_success
def parse_facts(facts, is_virtual):
    if is_virtual:
        model_name = " ".join((facts['manufacturer'], facts['virtual']))
        model_type = DeviceType.virtual_server
        dev_name_parts = [model_name]
        if 'lsbdistdescription' in facts:
            dev_name_parts.append(facts['lsbdistdescription'])
        elif 'operatingsystem' in facts:
            dev_name_parts.append(facts['operatingsystem'])
            if 'operatingsystemrelease' in facts:
                dev_name_parts.append(facts['operatingsystemrelease'])
        dev_name = " ".join(dev_name_parts)
        try:
            mac = get_default_mac(facts)
        except ValueError, e:
            return False, "Invalid MAC address: {}".format(e)
        if not mac:
            return False, "Machine has no MAC addresses."
        sn = "".join(("VIRT0_", mac, '_', hashlib.md5(facts.get('sshdsakey',
            facts.get('sshrsakey', '#'))).hexdigest()[:8]))
    else:
        sn = facts.get('serialnumber')
        if sn in SERIAL_BLACKLIST:
            sn = None
        prod_name = facts.get('productname')
        manufacturer = facts.get('manufacturer')
        if not prod_name or not manufacturer:
            return False, "`productname` or `manufacturer` facts not "\
                    "available. `lshw` not present."
        if manufacturer and manufacturer in prod_name:
            model_name = prod_name
        else:
            model_name = "{} {}".format(manufacturer, prod_name)
        dev_name = model_name
        if DeviceType.blade_server.matches(model_name):
            model_type = DeviceType.blade_server
        else:
            model_type = DeviceType.rack_server
    ip_addresses, ethernets = handle_facts_ethernets(facts)
    dev = Device.create(sn=sn, model_name=model_name, model_type=model_type,
                        ethernets=ethernets, priority=SAVE_PRIORITY)
    dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
    assign_ips(dev, ip_addresses)
    try:
        _parse_prtconf(dev, facts['prtconf'], facts, is_virtual=is_virtual)
    except (KeyError, zlib.error) as e:
        pass
    try:
        _parse_smbios(dev, facts['smbios'], facts, is_virtual=is_virtual)
    except (KeyError, zlib.error) as e:
        pass
    handle_facts_disks(dev, facts, is_virtual=is_virtual)
    return dev, dev_name

def network_prtconf(as_string):
    return None, as_string

def _parse_prtconf(dev, prtconf, facts, is_virtual):
    prtconf, _ = network_prtconf(as_string=zlib.decompress(prtconf))

DENSE_SPEED_REGEX = re.compile(r'(\d+)\s*([GgHhKkMmZz]+)')

def _parse_smbios(dev, smbios, facts, is_virtual):
    smbios, _ = hardware.smbios(as_string=zlib.decompress(smbios))
    # memory
    for memory in smbios.get('MEMDEVICE', ()):
        try:
            size, size_units = memory.get('Size', '').split(' ', 1)
            size = int(size)
            size /= units.size_divisor[size_units]
            size = int(size)
        except ValueError:
            continue # empty slot
        for split_key in ('BANK', 'Slot '):
            try:
                bank = memory.get('Bank Locator').split(split_key)[1]
                bank = int(bank) + 1
                break
            except (IndexError, ValueError):
                bank = None # unknown bank
        if bank is None:
            continue
        mem, created = Memory.concurrent_get_or_create(device=dev, index=bank)
        if created:
            mem.speed = 0
        mem.label = "{} {}".format(memory.get('Device Locator',
            memory.get('Location Tag', 'DIMM')), memory.get('Part Number', ''))
        mem.size = size
        manufacturer = memory.get('Manufacturer', 'Manufacturer')
        if not manufacturer.startswith('Manufacturer'):
            mem.label = manufacturer + ' ' + mem.label
        family = 'Virtual' if is_virtual else ''
        mem.model, c = ComponentModel.concurrent_get_or_create(
            size=mem.size, speed=0, type=ComponentType.memory.id,
            family=family, extra_hash='')
        name = 'RAM %dMiB' % mem.size
        if family:
            name = '%s %s' % (family, name)
        mem.model.name = name
        mem.model.save(priority=SAVE_PRIORITY)
        mem.save(priority=SAVE_PRIORITY)
    # CPUs
    detected_cpus = {}
    for cpu in smbios.get('PROCESSOR', ()):
        m = DENSE_SPEED_REGEX.match(cpu.get('Maximum Speed', ''))
        if not m:
            continue
        if 'enabled' not in cpu.get('Processor Status', ''):
            continue
        speed = int(m.group(1))
        speed_units = m.group(2)
        speed /= units.speed_divisor[speed_units]
        speed = int(speed)
        label = cpu['Location Tag']
        family = cpu['Family']
        if '(other)' in family:
            family = cpu['Manufacturer']
        index_parts = []
        for cpu_part in cpu['Location Tag'].replace('CPU', '').split():
            try:
                index_parts.append(int(cpu_part.strip()))
            except ValueError:
                continue
        index = reduce(lambda x, y: x*y, index_parts)
        extra = "CPUID: {}".format(cpu['CPUID'])
        model, c = ComponentModel.concurrent_get_or_create(
            speed=speed, type=ComponentType.processor.id, extra=extra,
            extra_hash=hashlib.md5(extra).hexdigest(), family=family,
            cores=0)
        model.name = " ".join(cpu.get('Version', family).split())
        model.save(priority=SAVE_PRIORITY)
        detected_cpus[index] = label, model
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

def handle_facts_ethernets(facts):
    ethernets = []
    ip_addresses = []
    for interface in facts['interfaces'].split(','):
        try:
            ip = network.validate_ip(facts['ipaddress_{}'.format(interface)])
            ip_addresses.append(ip)
        except (ValueError, KeyError):
            pass
        mac = facts.get('macaddress_{}'.format(interface))
        if not mac:
            continue
        label = 'Ethernet {}'.format(interface)
        ethernets.append(Eth(label, mac, speed=None))
    return ip_addresses, ethernets

def handle_facts_disks(dev, facts, is_virtual=False):
    disks = {}
    _cur_key = None
    for k, v in facts.iteritems():
        if not k.startswith('disk_'):
            continue
        k = k[5:]
        if k.endswith('_product'):
            _cur_key = 'product'
            k = k[:-8]
        elif k.endswith('_revision'):
            _cur_key = 'revision'
            k = k[:-9]
        elif k.endswith('_size'):
            _cur_key = 'size'
            k = k[:-5]
        elif k.endswith('_vendor'):
            _cur_key = 'vendor'
            k = k[:-7]
        elif k.endswith('_serial'):
            _cur_key = 'serial'
            k = k[:-7]
        else:
            continue
        disks.setdefault(k, {})[_cur_key] = v.strip()
    for label, disk in disks.iteritems():
        try:
            if 'size' not in disk or not int(disk['size']):
                continue
        except ValueError:
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        sn = disk.get('serial', '').strip()
        if sn:
            stor, created = Storage.concurrent_get_or_create(device=dev,
                sn=sn)
        else:
            stor, created = Storage.concurrent_get_or_create(device=dev,
                mount_point=label, sn=None)
        stor.size = disk['size'] = int(int(disk['size']) / 1024 / 1024)
        stor.label = '{} {} {}'.format(disk['vendor'].strip(),
            disk['product'].strip(), disk['revision'].strip())
        extra = """Vendor: {vendor}
Product: {product}
Firmware Revision: {revision}
Size: {size}""".format(**disk)
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, speed=0, type=ComponentType.disk.id,
            family=disk['vendor'].strip(),
            extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)


