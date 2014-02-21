#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    GenericComponent,
    SERIAL_BLACKLIST,
)
from ralph.discovery.models_history import DiscoveryWarning


INVENTORY_RE = re.compile(
    r'(NAME|Name):\s*(?P<name>"[^"]*"|\S*)\s*,\s*DESCR:\s*'
    r'(?P<descr>"[^"]*"|\S*)\s*PID:\s*(?P<pid>"[^"]*"|\S*)\s*,\s*'
    r'VID:\s*(?P<vid>"[^"]*"|\S*)\s*,\s*SN:\s*(?P<sn>"[^"]*"|\S*)\s*',
    re.U | re.M,
)


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
    if (
        pid.startswith('WS-X') or
        pid.startswith('WS-SUP') or
        pid.startswith('WS-C') or
        pid.startswith('RSP720') or
        pid.startswith('CISCO') or
        pid.startswith('WS-SVC')
    ):
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


def cisco_component(dev, inv, ip_address=None):
    comp_type = cisco_type(inv['pid'])
    name = inv['descr']
    if not name.lower().startswith('cisco'):
        name = 'Cisco %s' % name
    model, created = ComponentModel.create(
        comp_type,
        family=inv['pid'],
        name=name,
        priority=0,   # FIXME: why 0?
    )
    comp, created = GenericComponent.concurrent_get_or_create(
        sn=inv['sn'],
        defaults={
            'device': dev,
        },
    )
    if comp.device == dev:
        comp.model = model
        comp.label = inv['name'][:255]
        comp.save()
    elif ip_address:
        DiscoveryWarning(
            message="GenericComponent(id={}) belongs to Device(id={})".format(
                comp.id,
                comp.device.id,
            ),
            plugin=__name__,
            device=dev,
            ip=ip_address,
        ).save()
        comp = None
    else:
        comp = None
    return comp
