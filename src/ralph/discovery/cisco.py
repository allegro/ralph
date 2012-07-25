#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import hashlib

from ralph.discovery.models import (SERIAL_BLACKLIST,
                                    ComponentModel, GenericComponent, ComponentType)

INVENTORY_RE = re.compile(
r"""(NAME|Name):\s*(?P<name>"[^"]*"|\S*)\s*,\s*DESCR:\s*(?P<descr>"[^"]*"|\S*)\s*
PID:\s*(?P<pid>"[^"]*"|\S*)\s*,\s*VID:\s*(?P<vid>"[^"]*"|\S*)\s*,\s*SN:\s*(?P<sn>"[^"]*"|\S*)\s*""", re.U|re.M)

def cisco_inventory(raw):
    for match in INVENTORY_RE.finditer(raw):
        d = match.groupdict()
        if d['sn'] in SERIAL_BLACKLIST:
            d['sn'] = None
        d['descr'] = d['descr'].strip('"')
        d['name'] = d['name'].strip('"')
        yield d

def cisco_type(pid):
    comp_type = ComponentType.unknown
    if (pid.startswith('WS-X') or
        pid.startswith('WS-SUP') or
        pid.startswith('WS-C') or
        pid.startswith('RSP720') or
        pid.startswith('CISCO') or
        pid.startswith('WS-SVC')):
        comp_type = ComponentType.management
    elif pid.startswith('WS-F') or pid.startswith('7600-'):
        comp_type = ComponentType.expansion
    elif pid.startswith('WS-CAC') or pid.startswith('PWR-') or '-PWR-' in pid:
        comp_type = ComponentType.power
    elif (pid.startswith('XENPAK-10GB') or
          pid.startswith('SFP-') or
          '-2X10GE-' in pid or
          pid.startswith('X2-10GB')):
        comp_type = ComponentType.ethernet
    elif pid.endswith('-E-FAN'):
        comp_type = ComponentType.cooling
    return comp_type

def cisco_component(dev, inv):
    extra = '' # '\n'.join('%s: %s' % i for i in inv.iteritems())
    comp_type = cisco_type(inv['pid'])
    model, created = ComponentModel.concurrent_get_or_create(
        type=comp_type.id, size=0, speed=0, cores=0, family=inv['pid'],
        extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
    name = inv['descr']
    if not name.lower().startswith('cisco'):
        name = 'Cisco %s' % name
    if created:
        model.name = name[:50]
        model.save()
    elif model.name != name[:50]:
        model.name = name[:50]
        model.save()
    comp, created = GenericComponent.concurrent_get_or_create(
            sn=inv['sn'], device=dev)
    comp.model = model
    comp.label = inv['name'][:255]
    comp.save()
    return comp

