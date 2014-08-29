#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import Device
from ralph.util.views import jsonify


@jsonify
def servertree(request, hostname=None):
    response = []
    qs = Device.objects.exclude(venture_role=None)
    if hostname:
        qs = qs.filter(ipaddress__hostname=hostname)
    for device in qs.select_related():
        for ip in device.ipaddress_set.exclude(is_management=True):
            response.append(dict(
                name=ip.hostname or ip.address,
                role=unicode(
                    device.venture_role) if device.venture_role else device.role,
                is_legacy=not device.venture_role,
                model=unicode(device.model),
                venture_symbol=device.venture.symbol if device.venture else None,
                venture_name=unicode(
                    device.venture) if device.venture else None,
            ))
    return response
