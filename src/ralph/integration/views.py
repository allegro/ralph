#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.account.models import Perm, ralph_permission
from ralph.discovery.models import Device
from ralph.util.views import jsonify
from django.utils.translation import ugettext_lazy as _


perms = [
    {
        'perm': Perm.has_core_access,
        'msg': _("You don't have permissions for this resource."),
    },
]


@ralph_permission(perms)
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
