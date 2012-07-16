#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import network
from ralph.util import plugin
from ralph.discovery.models import IPAddress


@plugin.register(chain='discovery', requires=None)
def ping(**kwargs):
    ip = kwargs['ip']
    is_up = False
    if network.ping(str(ip)) is None:
        message = 'down.'
    else:
        is_up = True
        message = 'up!'
        ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
        hostname = network.hostname(ip)
        if hostname:
            ip_address.hostname = hostname
            ip_address.dns_info = '\n'.join(network.descriptions(hostname))
        kwargs['community'] = ip_address.snmp_community
        ip_address.save(update_last_seen=True)
    return is_up, message, kwargs

