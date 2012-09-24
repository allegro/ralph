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

from ralph.util import network, Eth
from ralph.discovery.models import (DeviceType, Device, OperatingSystem,
    ComponentModel, ComponentType, Storage, SERIAL_BLACKLIST,
    DISK_VENDOR_BLACKLIST, DISK_PRODUCT_BLACKLIST)

from .util import assign_ips, get_default_mac
from ralph.discovery import hardware


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
    except KeyError as e:
        pass
    handle_facts_disks(dev, facts, is_virtual=is_virtual)
    return dev, dev_name

def network_prtconf(as_string):
    return None, as_string

def _parse_prtconf(dev, prtconf, facts, is_virtual):
    prtconf, _ = network_prtconf(as_string=zlib.decompress(prtconf))

def _parse_smbios(dev, data, facts, is_virtual):
    try:
        data = zlib.decompress(data)
    except zlib.error:
        pass
    smb = hardware.parse_smbios(data)
    hardware.handle_smbios(dev, smb, is_virtual, SAVE_PRIORITY)

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
        stor.model.name = '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)

@nested_commit_on_success
def handle_facts_os(dev, facts, is_virtual=False):
    try:
        os_name = "%s %s" % (facts['operatingsystem'],
                             facts['operatingsystemrelease'])
        family = facts['kernel']
        os_version = facts.get('kernelrelease', '')
    except KeyError:
        return
    os = OperatingSystem.create(dev=dev, os_name=os_name, version=os_version,
                                family=family)
    memory_size = None
    try:
        memory_size, unit = re.split('\s+', facts['memorysize'].lower())
        if unit == 'tb':
            memory_size = int(float(memory_size) * 1024 * 1024)
        elif unit == 'gb':
            memory_size = int(float(memory_size) * 1024)
        elif unit == 'mb' or unit == 'mib':
            memory_size = int(memory_size)
    except (KeyError, ValueError):
        pass
    os.memory = memory_size
    if is_virtual:
        os.cores_count = facts.get('processorcount', None)
    else:
        os.cores_count = facts.get('physicalprocessorcorecount', None)
    os.save(priority=SAVE_PRIORITY)
