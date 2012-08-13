#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.lang import Null, nullify
from lck.xml import etree_to_dict
import lck.xml.converters
from lxml import etree as ET


SMBIOS_BANNER = 'ID    SIZE TYPE'


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


def smbios(as_string):
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
    return smb, as_string


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

def lshw(as_string):
    parser = ET.ETCompatXMLParser(recover=True)
    response = ET.fromstring(as_string, parser=parser)
    if response.tag.upper() != 'NODE':
        return None, as_string
    for element in response.findall('.//'):
        for k in element.attrib.keys():
            try:
                v = element.attrib[k]
            except UnicodeDecodeError:
                continue # value has bytes not possible to decode with UTF-8
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
    return nullify(etree_to_dict(response, _converters=[_nullify, int, float,
        lck.xml.converters._datetime,
        lck.xml.converters._datetime_strip_tz]))[1], as_string


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
