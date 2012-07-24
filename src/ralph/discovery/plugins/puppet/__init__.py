#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovery configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import hashlib
import random
import re
import time

from lck.django.common import nested_commit_on_success
import MySQLdb
from django.conf import settings

from ralph.util import network, plugin, units
from ralph.discovery.models import (IPAddress, ComponentModel, ComponentType,
    Storage, DiskShare, DiskShareMount, DISK_VENDOR_BLACKLIST,
    DISK_PRODUCT_BLACKLIST)
from ralph.discovery.hardware import normalize_wwn

from .facts import parse_facts
from .lshw import parse_lshw
from .util import connect_db, get_ip_hostname_sets


SAVE_PRIORITY = 51


@plugin.register(chain='discovery', requires=['ping'], priority=200)
def puppet(**kwargs):
    if not settings.PUPPET_DB_URL:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    ip_set, hostname_set = get_ip_hostname_sets(ip)
    db = connect_db()
    facts = get_all_facts_by_ip_set(db, ip_set)
    if not facts and hostname_set:
        facts = get_all_facts_by_hostname_set(db, hostname_set)
    if not facts:
        return False, "host config not found.", kwargs

    try:
        is_virtual = is_host_virtual(facts)
        try:
            lshw = facts['lshw']
        except KeyError:
            dev, dev_name = parse_facts(facts, is_virtual)
        else:
            dev, dev_name = parse_lshw(lshw, facts, is_virtual)
    except MySQLdb.OperationalError as e:
        if e.args[0] in (1205, 1213) and 'try restarting transaction' in e.args[1]:
            time.sleep(random.choice(range(10))+1)
            raise plugin.Restart(unicode(e), kwargs)
        raise
    if not dev:
        return False, dev_name, kwargs

    parse_wwn(facts, dev)
    parse_smartctl(facts, dev)
    parse_hpacu(facts, dev)
    parse_megaraid(facts, dev)
    parse_uptime(facts, dev)

    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device, message = dev, dev_name
    if created:
        ip_address.hostname = network.hostname(ip_address.address)
    ip_address.last_puppet = datetime.datetime.now()
    ip_address.save(update_last_seen=True) # no priorities for IP addresses
    return True, message, kwargs

def get_all_facts_by_ip_set(db, ip_set):
    facts = None
    for ip in ip_set:
        rows = db.execute("""SELECT fn.name, fv.value
                            FROM hosts h, fact_values fv, fact_names fn
                            WHERE h.ip=%s AND fv.host_id=h.id
                            AND fv.fact_name_id=fn.id""", ip)
        _facts = dict(rows.fetchall())
        if _facts:
            if _facts['virtual'] == 'zone':
                continue
            if not facts:
                facts = _facts
            else:
                raise ValueError("more than 1 machine reported by Puppet for "
                    "this IP set: {}".format(ip_set))
    return facts

def get_all_facts_by_hostname_set(db, hostname_set):
    facts = None
    for hostname in hostname_set:
        rows = db.execute("""SELECT fn.name, fv.value
                            FROM hosts h, fact_values fv, fact_names fn
                            WHERE h.name=%s AND fv.host_id=h.id
                            AND fv.fact_name_id=fn.id""", hostname)
        _facts = dict(rows.fetchall())
        if _facts:
            if not facts:
                facts = _facts
            else:
                raise ValueError("more than 1 machine reported by Puppet for "
                    "this hostname set: {}".format(hostname_set))
    return facts

def is_host_virtual(facts):
    is_virtual = facts.get('virtual', 'physical') not in ('physical',
        'openvz', 'openvzhn')
    if facts.get('manufacturer') == 'Bochs' and not is_virtual:
        facts['virtual'] = 'virtual'
        is_virtual = True
    return is_virtual

@nested_commit_on_success
def parse_wwn(facts, dev):
    def make_mount(wwn):
        try:
            share = DiskShare.objects.get(wwn=wwn)
        except DiskShare.DoesNotExist:
            return None
        mount, created = DiskShareMount.concurrent_get_or_create(
                share=share, device=dev)
        return mount
    wwns = []
    for key, wwn in facts.iteritems():
        if not key.startswith('wwn_mpath'):
            continue
        wwns.append(normalize_wwn(wwn))
    for wwn in wwns:
        mount = make_mount(wwn)
        if not mount:
            continue
        path = key.replace('wwn_', '')
        mount.volume = '/dev/mapper/%s' % path
        mount.save(priority=SAVE_PRIORITY)
    dev.disksharemount_set.filter(server=None).exclude(share__wwn__in=wwns).delete()

HPACU_GENERAL_REGEX = re.compile(r'hpacu_([^_]+)__(.+)')
HPACU_LOGICAL_PHYSICAL_REGEX = re.compile(r'([^_]+)__(.+)')

@nested_commit_on_success
def parse_hpacu(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = HPACU_GENERAL_REGEX.match(k)
        if not m:
            continue
        n = HPACU_LOGICAL_PHYSICAL_REGEX.match(m.group(2))
        physical_disk = n.group(1) if n else None
        property = n.group(2) if n else m.group(2)
        if not physical_disk:
            continue
        disks.setdefault(physical_disk, {})[property] = value.strip()
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial_number'):
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev,
            sn=disk['serial_number'])
        stor.device = dev
        size_value, size_unit = disk['size'].split()
        stor.size = int(float(size_value) / units.size_divisor[size_unit])
        stor.speed = int(disk.get('rotational_speed', 0))
        stor.label = '{} {}'.format(' '.join(disk['model'].split()),
            disk['interface_type'])
        disk_default = dict(
            model = 'unknown',
            firmware_revision = 'unknown',
            interface_type = 'unknown',
            size = 'unknown',
            rotational_speed = 'unknown',
            status = 'unknown',
        )
        disk_default.update(disk)
        extra = """Model: {model}
Firmware Revision: {firmware_revision}
Interface: {interface_type}
Size: {size}
Rotational Speed: {rotational_speed}
Status: {status}""".format(**disk_default)
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, speed=stor.speed, type=ComponentType.disk.id,
            family='', extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)

SMARTCTL_REGEX = re.compile(r'smartctl_([^_]+)__(.+)')

@nested_commit_on_success
def parse_smartctl(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = SMARTCTL_REGEX.match(k)
        if not m:
            continue
        disk = m.group(1)
        property = m.group(2)
        disks.setdefault(disk, {})[property] = value.strip()
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial_number') or disk.get('device_type') != 'disk':
            continue
        if {'user_capacity', 'vendor', 'product', 'transport_protocol'} - \
                set(disk.keys()):
            # not all required keys present
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev,
            sn=disk['serial_number'])
        stor.device = dev
        size_value, size_unit, rest = disk['user_capacity'].split(' ', 2)
        size_value = size_value.replace(',', '')
        stor.size = int(int(size_value) / units.size_divisor[size_unit])
        stor.speed = int(disk.get('rotational_speed', 0))
        label_meta = [' '.join(disk['vendor'].split()), disk['product']]
        if 'transport_protocol' in disk:
            label_meta.append(disk['transport_protocol'])
        stor.label = ' '.join(label_meta)
        disk_default = dict(
            vendor = 'unknown',
            product = 'unknown',
            revision = 'unknown',
            transport_protocol = 'unknown',
            user_capacity = 'unknown',
        )
        disk_default.update(disk)
        extra = """Model: {vendor} {product}
Firmware Revision: {revision}
Interface: {transport_protocol}
Size: {user_capacity}
""".format(**disk_default)
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, speed=stor.speed, type=ComponentType.disk.id,
            family='', extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)

MEGARAID_REGEX = re.compile(r'megacli_([^_]+)_([^_]+)__(.+)')

@nested_commit_on_success
def parse_megaraid(facts, dev):
    disks = {}
    for k, value in facts.iteritems():
        m = MEGARAID_REGEX.match(k)
        if not m:
            continue

        controller = m.group(1)
        disk = m.group(2)
        property = m.group(3)
        disks.setdefault((controller, disk), {})[property] = value.strip()
    for (controller_handle, disk_handle), disk in disks.iteritems():
        disk['vendor'], disk['product'], disk['serial_number'] = \
                _handle_inquiry_data(disk.get('inquiry_data', ''),
                        controller_handle, disk_handle)

        if not disk.get('serial_number') or disk.get('media_type') not in ('Hard Disk Device',
                'Solid State Device'):
            continue
        if {'coerced_size', 'vendor', 'product', 'pd_type'} - \
                set(disk.keys()):
            # not all required keys present
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev,
            sn=disk['serial_number'])
        stor.device = dev
        size_value, size_unit, rest = disk['coerced_size'].split(' ', 2)
        size_value = size_value.replace(',', '')
        stor.size = int(float(size_value) / units.size_divisor[size_unit])
        stor.speed = int(disk.get('rotational_speed', 0))
        label_meta = [' '.join(disk['vendor'].split()), disk['product']]
        if 'pd_type' in disk:
            label_meta.append(disk['pd_type'])
        stor.label = ' '.join(label_meta)
        disk_default = dict(
            vendor = 'unknown',
            product = 'unknown',
            device_firmware_level = 'unknown',
            pd_type = 'unknown',
            coerced_size = 'unknown',
        )
        disk_default.update(disk)
        extra = """Model: {vendor} {product}
Firmware Revision: {device_firmware_level}
Interface: {pd_type}
Size: {coerced_size}
""".format(**disk_default)
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, speed=stor.speed, type=ComponentType.disk.id,
            family='', extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)

@nested_commit_on_success
def parse_uptime(facts, dev):
    try:
        uptime = int(facts['uptime_seconds'])
    except (KeyError, TypeError, ValueError):
        uptime = None
    dev.uptime = uptime
    dev.save()

INQUIRY_REGEXES = (
    re.compile(r'^(?P<vendor>OCZ)-(?P<sn>[a-zA-Z0-9]{16})OCZ-(?P<product>\S+)\s+.*$'),
    re.compile(r'^(?P<vendor>(FUJITSU|TOSHIBA))\s+(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]{16})$'),
    re.compile(r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[^G]+G)(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(r'^(?P<sn>[a-zA-Z0-9]{18})\s+(?P<vendor>INTEL)\s+(?P<product>[a-zA-Z0-9]+)\s+.*$'),
    re.compile(r'^(?P<vendor>IBM)-(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(r'^(?P<vendor>HP)\s+(?P<product>[a-zA-Z0-9]{11})\s+(?P<sn>[a-zA-Z0-9]{12})$'),
    re.compile(r'^(?P<vendor>HITACHI)\s+(?P<product>[a-zA-Z0-9]{15})(?P<sn>[a-zA-Z0-9]{15})$'),
)

def _handle_inquiry_data(raw, controller, disk):
    for regex in INQUIRY_REGEXES:
        m = regex.match(raw)
        if m:
            return m.group('vendor'), m.group('product'), m.group('sn')
    raise ValueError("Incompatible inquiry_data for disk {}/{}: {}"
        "".format(controller, disk, raw))
