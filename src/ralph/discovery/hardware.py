#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import re
import zlib

from ralph.util import units
from ralph.discovery.models import (Memory, Processor, ComponentModel,
                                    ComponentType)



SMBIOS_BANNER = 'ID    SIZE TYPE'
DENSE_SPEED_REGEX = re.compile(r'(\d+)\s*([GgHhKkMmZz]+)')


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
    """

    wwn = wwn.replace(':', '').replace(' ', '').replace('.', '').strip().upper()
    if len(wwn) == 16:
        # 3PAR
        pass
    elif len(wwn) == 17:
        # 3PAR - multipath
        wwn = wwn[1:]
    elif len(wwn) == 33 and wwn[-6:] == '000000' and wwn[8:11] == '000':
        # MSA - multipath
        wwn = wwn[11:-6]
    elif len(wwn) == 32 and wwn[-6:] == '000000' and wwn[12:16] == '0000':
        # MSA
        wwn = wwn[6:12] + wwn[16:-6]
    elif len(wwn) == 32 and wwn.startswith((
            '600A0B80', # IBM
        )):
        pass
    elif len(wwn) == 33 and wwn.startswith((
            '3600A0B80', # IBM - multipath
            '3600508B1', # HP logical volume - multipath
            '3600144F0', # SUN - multipath
        )):
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
        mem.model.save(priority=priority)
        mem.save(priority=priority)
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
        model.save(priority=priority)
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


def get_disk_shares(ssh):
    stdin, stdout, stderr = ssh.exec_command("multipath -l")
    pvs = {}
    for line in stdout.readlines():
        line = line.strip()
        if not line.startswith('mpath'):
            continue
        try:
            path, wwn, pv, model = line.strip().split(None, 3)
        except ValueError:
            wwn, pv, model = line.strip().split(None, 2)
            path = None
        wwn  = normalize_wwn(wwn.strip('()'))
        pvs['/dev/%s' % pv] = wwn
        if path:
            pvs['/dev/mapper/%s' % path] = wwn
    stdin, stdout, stderr = ssh.exec_command("pvs --noheadings --units M")
    vgs = {}
    for line in stdout.readlines():
        pv, vg, fmt, attr, psize, pfree = line.split(None, 5)
        vgs[vg] = pv
    stdin, stdout, stderr = ssh.exec_command("lvs --noheadings --units M")
    storage = {}
    for line in stdout.readlines():
        lv, vg, attr, size, rest = (line + ' x').strip().split(None, 4)
        size = int(float(size.strip('M')))
        try:
            wwn = pvs[vgs[vg]]
        except KeyError:
            continue
        storage[lv] = (wwn, size)
    return storage
