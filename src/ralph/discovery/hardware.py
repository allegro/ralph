#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from ralph.util import units, parse
from ralph.discovery.models import (
    Memory, Processor, ComponentModel,
    ComponentType, Storage, DISK_VENDOR_BLACKLIST, DISK_PRODUCT_BLACKLIST,
    Device, DeviceType
)


SMBIOS_BANNER = 'ID    SIZE TYPE'
DENSE_SPEED_REGEX = re.compile(r'(\d+)\s*([GgHhKkMmZz]+)')
INQUIRY_REGEXES = (
    re.compile(
        r'^(?P<vendor>OCZ)-(?P<sn>[a-zA-Z0-9]{16})OCZ-(?P<product>\S+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>(FUJITSU|TOSHIBA))\s+(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]{16})$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[^G]+G)(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[0-9]+SS)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[A-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<sn>[a-zA-Z0-9]{18})\s+(?P<vendor>INTEL)\s+(?P<product>[a-zA-Z0-9]+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>IBM)-(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>HP)\s+(?P<product>[a-zA-Z0-9]{11})\s+(?P<sn>[a-zA-Z0-9]{12})$'),
    re.compile(
        r'^(?P<vendor>HITACHI)\s+(?P<product>[a-zA-Z0-9]{15})(?P<sn>[a-zA-Z0-9]{15})$'),
    re.compile(
        r'^(?P<vendor>HITACHI)\s+(?P<product>[a-zA-Z0-9]{15})\s+(?P<sn>[a-zA-Z0-9]{12})$'),
    re.compile(
        r'^(?P<sn>[a-zA-Z0-9]{15})\s+(?P<vendor>Samsung)\s+(?P<product>[a-zA-Z0-9\s]+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>WD)\s+(?P<product>WD[A-Z0-9]{8})\s+(?P<sn>[a-zA-Z0-9]{16})$'),
)


class Error(Exception):
    pass


class DMIDecodeError(Error):
    pass


def normalize_wwn(wwn):
    """
    >>> normalize_wwn('50002ac2859a04c1') # 3PAR
    u'50002AC2859A04C1'
    >>> normalize_wwn('350002ac2859a04c1') # 3PAR - multipath
    u'50002AC2859A04C1'
    >>> normalize_wwn('3600508B1001030353432464243301000') # HP logical volume - multipath
    u'600508B1001030353432464243301000'
    >>> normalize_wwn('3600c0ff000d81e2cca8cbd4c01000000') # HP MSA - multipath
    u'D81E2CCA8CBD4C01'
    >>> normalize_wwn('00c0ffd81e2c0000ca8cbd4c01000000') # HP MSA
    u'D81E2CCA8CBD4C01'
    >>> normalize_wwn('3600a0b8000119ca80000574f4cfc5084') # IBM - multipath
    u'600A0B8000119CA80000574F4CFC5084'
    >>> normalize_wwn('60:0a:0b:80:00:11:9c:a8:00:00:57:4f:4c:fc:50:84') # IBM
    u'600A0B8000119CA80000574F4CFC5084'
    >>> normalize_wwn('3600144f01ef1490000004c08ed6f0008') # SUN - multipath
    u'600144F01EF1490000004C08ED6F0008'
    >>> normalize_wwn('36000402001d81b697962865b00000000') # NEXSAN
    u'36000402001D81B697962865B'
    """

    wwn = wwn.replace(':', '').replace(
        ' ', '').replace('.', '').strip().upper()
    if len(wwn) == 16:
        # 3PAR
        pass
    elif len(wwn) == 17:
        # 3PAR - multipath
        wwn = wwn[1:]
    elif len(wwn) == 33 and wwn[-6:] == '000000' and wwn[8:11] == '000':
        # MSA - multipath
        wwn = wwn[11:-6]
    elif len(wwn) == 33 and wwn[-8:] == '00000000' and wwn.startswith(
        '36000402'
    ):
        # NEXSAN
        wwn = wwn[0:-8]
    elif len(wwn) == 32 and wwn[-6:] == '000000' and wwn[12:16] == '0000':
        # MSA
        wwn = wwn[6:12] + wwn[16:-6]
    elif len(wwn) == 32 and wwn.startswith(('600A0B80',)):
        # IBM
        pass
    elif len(wwn) == 33 and wwn.startswith(
        (
            '3600A0B80',  # IBM - multipath
            '3600508B1',  # HP logical volume - multipath
            '3600144F0',  # SUN - multipath
        )
    ):
        wwn = wwn[1:]
    else:
        raise ValueError('Unknown WWN format %r' % wwn)
    return wwn


def parse_smbios(as_string):
    if not as_string.startswith(SMBIOS_BANNER):
        raise ValueError("Incompatible SMBIOS answer.")
    smb = {}
    current = None
    for line in as_string.split('\n'):
        if line == SMBIOS_BANNER:
            if current:
                ctype = current['__TYPE__']
                del current['__TYPE__']
                smb.setdefault(ctype, []).append(current)
                current = None
        elif current is None:
            for token in line.split():
                if token.startswith('SMB_TYPE_'):
                    current = {'__TYPE__': token[9:]}
                    break
        else:
            if ':' in line:
                key, value = line.split(':', 1)
                current[key.strip()] = value.strip()
            else:
                current.setdefault('capabilities', []).append(line)
    return smb


def handle_smbios(dev, smbios, is_virtual=False, priority=0):
    # memory
    for memory in smbios.get('MEMDEVICE', ()):
        try:
            size, size_units = memory.get('Size', '').split(' ', 1)
            size = int(size)
            size /= units.size_divisor[size_units]
            size = int(size)
        except ValueError:
            continue  # empty slot
        for split_key in ('BANK', 'Slot '):
            try:
                bank = memory.get('Bank Locator').split(split_key)[1]
                bank = int(bank) + 1
                break
            except (IndexError, ValueError):
                bank = None  # unknown bank
        if bank is None:
            continue
        mem, created = Memory.concurrent_get_or_create(device=dev, index=bank)
        if created:
            mem.speed = 0
        mem.label = "{} {}".format(
            memory.get('Device Locator', memory.get('Location Tag', 'DIMM')),
            memory.get('Part Number', '')
        )
        mem.size = size
        manufacturer = memory.get('Manufacturer', 'Manufacturer')
        if not manufacturer.startswith('Manufacturer'):
            mem.label = manufacturer + ' ' + mem.label
        family = 'Virtual' if is_virtual else ''
        mem.model, c = ComponentModel.create(
            ComponentType.memory,
            size=mem.size,
            family=family,
            priority=priority,
        )
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
        index = reduce(lambda x, y: x * y, index_parts)
        model, c = ComponentModel.create(
            ComponentType.processor,
            family=family,
            speed=speed,
            name=" ".join(cpu.get('Version', family).split()),
            priority=priority,
        )
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
        cpu.save(priority=priority)


def _get_info_from_multipath(ssh):
    stdin, stdout, stderr = ssh.exec_command("multipath -l")
    available_shares = []
    pvs = {}
    current_share = {}
    for line in stdout.readlines():
        line = line.strip()
        if 'dm multipath kernel driver version too old' in line.lower():
            break
        if 'dm multipath kernel driver not loaded' in line.lower():
            break
        if line.startswith((r'\_', r'\[', r'`-', r'|')):
            continue
        if 'size=' not in line:
            try:
                path, wwn, pv, model = line.split(None, 3)
            except ValueError:
                wwn, pv, model = line.split(None, 2)
                path = None
            wwn = wwn.strip('()')
            if not path:
                path = wwn
            try:
                wwn = normalize_wwn(wwn)
            except ValueError:
                # continue when could not normalize wwn (ex. when there
                # are multipath warnings at the beginning of the output)
                continue
            current_share = {
                'pv': pv,
                'wwn': wwn
            }
            pvs['/dev/%s' % pv] = wwn
            if path:
                pvs['/dev/mapper/%s' % path] = wwn
        else:
            if not current_share:
                # if current share was not set because of ValueError during
                # wwn normalization
                continue
            line = line.replace('][', ' ')
            size_info = line.split(None, 1)[0].split('=')[1]
            size = None
            if 'M' in size_info:
                size = int(float(size_info.strip('M')))
            elif 'G' in size_info:
                size = int(float(size_info.strip('G'))) * 1024
            elif 'T' in size_info:
                size = int(float(size_info.strip('T'))) * 1024 * 1024
            if size:
                current_share['size'] = size
            available_shares.append(current_share)
            current_share = {}
    return pvs, available_shares


def _get_info_from_pvs(ssh, pvs):
    stdin, stdout, stderr = ssh.exec_command(
        "pvs --noheadings --units M --separator '|'"
    )
    vgs = {}
    for line in stdout.readlines():
        pv, vg, fmt, attr, size, rest = line.split('|', 5)
        pv = pv.strip()
        vg = vg.strip()
        mount_size = int(float(size.strip('M')))
        if not vg:
            continue
        try:
            wwn = pvs[pv]
        except KeyError:
            # sometimes pv is a link and needs to be dereferenced
            stdin, stdout, stderr = ssh.exec_command(
                "readlink -f {}".format(pv)
            )
            pv_dereferenced = stdout.read().strip()
            if pv_dereferenced:
                try:
                    wwn = pvs[pv_dereferenced]
                    pv = pv_dereferenced
                except KeyError:
                    continue
        vgs[vg] = {
            'wwn': wwn,
            'mount_size': mount_size,
            'pv': pv,
        }
    return vgs


def get_disk_shares(ssh, include_logical_volumes=False):
    pvs, available_shares = _get_info_from_multipath(ssh)
    vgs = _get_info_from_pvs(ssh, pvs)

    storage = {}
    if not include_logical_volumes:
        parsed_wwns = set()
        for vg, mount_data in vgs.iteritems():
            storage[vg] = (mount_data['wwn'], mount_data['mount_size'])
            parsed_wwns.add(mount_data['wwn'])
        # sometimes shares are not mounted as physical devices...
        for share in available_shares:
            if share['wwn'] in parsed_wwns:
                continue
            storage[share['pv']] = (share['wwn'], share['size'])
        return storage

    # if include_logical_volumes == True then get addtional info from lvs
    stdin, stdout, stderr = ssh.exec_command("lvs --noheadings --units M")
    for line in stdout.readlines():
        lv, vg, attr, size, rest = (line + ' x').strip().split(None, 4)
        size = int(float(size.strip('M')))
        try:
            wwn = pvs[vgs[vg]['pv']]
        except KeyError:
            continue
        storage[lv] = (wwn, size)
    return storage


def handle_smartctl(dev, disks, priority=0):
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
        stor, created = Storage.concurrent_get_or_create(
            device=dev, sn=disk['serial_number'], mount_point=None,
        )
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
            vendor='unknown',
            product='unknown',
            revision='unknown',
            transport_protocol='unknown',
            user_capacity='unknown',
        )
        disk_default.update(disk)
        stor.model, c = ComponentModel.create(
            ComponentType.disk,
            size=stor.size,
            speed=stor.speed,
            family=stor.label,
            priority=priority,
        )
        stor.save(priority=priority)


def _handle_inquiry_data(raw, controller, disk):
    if not raw:
        return None, None, None
    for regex in INQUIRY_REGEXES:
        m = regex.match(raw)
        if m:
            return m.group('vendor'), m.group('product'), m.group('sn')
    raise ValueError(
        "Incompatible inquiry_data for disk {}/{}: {}".format(
            controller, disk, raw
        )
    )


def handle_megaraid(dev, disks, priority=0):
    for (controller_handle, disk_handle), disk in disks.iteritems():
        disk['vendor'], disk['product'], disk['serial_number'] = \
            _handle_inquiry_data(
                disk.get('inquiry_data', ''),
                controller_handle, disk_handle)

        if not disk.get('serial_number') or disk.get('media_type') not in (
                'Hard Disk Device', 'Solid State Device'):
            continue
        if {'coerced_size', 'vendor', 'product', 'pd_type'} - \
                set(disk.keys()):
            # not all required keys present
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        stor, created = Storage.concurrent_get_or_create(
            device=dev, sn=disk['serial_number'], mount_point=None,
        )
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
            vendor='unknown',
            product='unknown',
            device_firmware_level='unknown',
            pd_type='unknown',
            coerced_size='unknown',
        )
        disk_default.update(disk)
        stor.model, c = ComponentModel.create(
            ComponentType.disk,
            size=stor.size,
            speed=stor.speed,
            family=stor.label,
            priority=priority,
        )
        stor.save(priority=priority)


def handle_3ware(dev, disks, priority=0):
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial'):
            continue
        stor, created = Storage.concurrent_get_or_create(
            device=dev, sn=disk['serial'], mount_point=None,
        )
        stor.device = dev
        size_value, size_unit, trash = disk['capacity'].split(None, 2)
        stor.size = int(float(size_value) / units.size_divisor[size_unit])
        stor.label = disk['model']
        disk_default = dict(
            model='unknown',
            firmware_revision='unknown',
            interface_type='unknown',
            size='unknown',
            rotational_speed='unknown',
            status='unknown',
        )
        disk_default.update(disk)
        stor.model, c = ComponentModel.create(
            ComponentType.disk,
            size=stor.size,
            family=stor.label,
            priority=priority,
        )
        stor.save(priority=priority)


def handle_hpacu(dev, disks, priority=0):
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial_number'):
            continue
        stor, created = Storage.concurrent_get_or_create(
            device=dev, sn=disk['serial_number'], mount_point=None,
        )
        stor.device = dev
        size_value, size_unit = disk['size'].split()
        stor.size = int(float(size_value) / units.size_divisor[size_unit])
        stor.speed = int(disk.get('rotational_speed', 0))
        stor.label = '{} {}'.format(' '.join(disk['model'].split()),
                                    disk['interface_type'])
        disk_default = dict(
            model='unknown',
            firmware_revision='unknown',
            interface_type='unknown',
            size='unknown',
            rotational_speed='unknown',
            status='unknown',
        )
        disk_default.update(disk)
        stor.model, c = ComponentModel.create(
            ComponentType.disk,
            size=stor.size,
            speed=stor.speed,
            family=stor.label,
            priority=priority,
        )
        stor.save(priority=priority)


def parse_dmidecode(data):
    """Parse data returned by the dmidecode command into a dict."""

    p = parse.multi_pairs(data)

    def exclude(value, exceptions):
        if value not in exceptions:
            return value

    def num(value):
        if value is None or value.lower() == 'unknown':
            return None
        try:
            num, unit = value.split(None, 1)
        except ValueError:
            num = value
        return int(num)
    if 'System Information' not in p:
        raise DMIDecodeError('System information not found')
    result = {
        'model': p['System Information']['Product Name'],
        'sn': p['System Information']['Serial Number'],
        'uuid': p['System Information']['UUID'],
        'cpu': [{
            'label': cpu['Socket Designation'],
            'model': cpu['Version'],
            'speed': num(cpu['Current Speed']),
            'threads': num(cpu.get('Thread Count')),
            'cores': num(cpu.get('Core Count')),
            'family': cpu['Family'],
            '64bit': any('64-bit capable' in char
                         for char in cpu.getlist('Characteristics') if char),
            'flags': [f.keys() for f in cpu.getlist('Flags')
                      if f][0] if 'Flags' in cpu else [],
        } for cpu in p.getlist('Processor Information') if cpu],
        'mem': [{
            'label': mem['Locator'],
            'type': mem['Type'],
            'size': num(mem['Size']),
            'speed': num(exclude(mem.get('Speed'), {'Unknown'})),
        } for mem in p.getlist('Memory Device')
            if mem and mem.get('Size') != 'No Module Installed'],
    }
    return result


def handle_dmidecode(info, ethernets=(), priority=0):
    """Take the data collected by parse_dmidecode and apply it to a device."""

    # It's either a rack or a blade server, who knows?
    # We will let other plugins determine that.
    dev = Device.create(
        ethernets=ethernets, sn=info['sn'], uuid=info['uuid'],
        model_name='DMI ' + info['model'], model_type=DeviceType.unknown,
        priority=priority,
    )
    for i, cpu_info in enumerate(info['cpu']):
        model, created = ComponentModel.create(
            ComponentType.processor,
            speed=cpu_info['speed'] or 0,
            cores=cpu_info['cores'] or 0,
            family=cpu_info['family'],
            name=cpu_info['model'],
            priority=priority,
        )
        cpu, created = Processor.concurrent_get_or_create(device=dev,
                                                          index=i + 1)
        if created:
            cpu.label = cpu_info['label']
            cpu.model = model
            cpu.save()
    for cpu in dev.processor_set.filter(index__gt=i + 1):
        cpu.delete()
    for i, mem_info in enumerate(info['mem']):
        model, created = ComponentModel.create(
            ComponentType.memory,
            speed=mem_info['speed'] or 0,
            size=mem_info['size'] or 0,
            family=mem_info['type'],
            priority=priority,
        )
        mem, created = Memory.concurrent_get_or_create(device=dev, index=i + 1)
        if created:
            mem.label = mem_info['label']
            mem.model = model
            mem.save()
    for mem in dev.memory_set.filter(index__gt=i + 1):
        mem.delete()
    return dev
