#!/usr/bin/env python
# -*- coding: utf-8 -*-


from lck.django.common import nested_commit_on_success

from ralph.util import plugin
from ralph.discovery.models import IPAddress
from ralph.discovery.http import get_http_family


@nested_commit_on_success
def run_http(ip):
    family = get_http_family(ip)
    ip_address, created = IPAddress.concurrent_get_or_create(address=ip)
    ip_address.http_family = family
    ip_address.save(update_last_seen=True)
    return family


@plugin.register(chain='discovery', requires=['ping'], priority=201)
def http(**kwargs):
    ip = str(kwargs['ip'])
    try:
        name = run_http(ip)
    except Exception as e:
        if hasattr(e, 'code') and hasattr(e, 'reason'):
            message = 'Error %s: %s (%s)' % (e.code, e.reason)
        else:
            message = 'Error: %s' % unicode(e)
        return True, message, kwargs
    kwargs['http_family'] = name
    return True, name, kwargs
