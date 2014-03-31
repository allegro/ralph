#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.util import pricing
from ralph.discovery.models import IPAddress


@plugin.register(chain='postprocess', requires=['ping'])
def cache_price(ip, **kwargs):
    ip = str(ip)
    try:
        ipaddr = IPAddress.objects.select_related().get(address=ip)
    except IPAddress.DoesNotExist:
        return False, 'no device.', kwargs
    dev = ipaddr.device
    if dev is None:
        return False, 'no device.', kwargs
    pricing.device_update_cached(dev)
    return True, 'price=%.2f cost=%.2f, name=%s' % (dev.cached_price or 0,
                                                    dev.cached_cost or 0, dev.name), kwargs
