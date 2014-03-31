#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.django.common import nested_commit_on_success

from ralph.util import plugin, network
from ralph.discovery.models import Software, IPAddress

SAVE_PRIORITY = 20


@nested_commit_on_success
def _detect_software(ip, dev, http_family):
    detected = []
    if network.check_tcp_port(ip, 1521):
        detected.append('Oracle')
        Software.create(
            dev,
            'oracle',
            'Oracle',
            family='Database',
            priority=SAVE_PRIORITY
        )
    else:
        dev.software_set.filter(path='oracle').all().delete()
    if network.check_tcp_port(ip, 3306):
        detected.append('MySQL')
        Software.create(
            dev,
            'mysql',
            'MySQL',
            family='Database',
            priority=SAVE_PRIORITY
        )
    else:
        dev.software_set.filter(path='mysql').all().delete()
    if network.check_tcp_port(ip, 80) or network.check_tcp_port(ip, 443):
        detected.append('WWW')
        Software.create(dev,
                        'www',
                        'WWW',
                        label=http_family,
                        family='WWW',
                        priority=SAVE_PRIORITY
                        )
    else:
        dev.software_set.filter(path='www').all().delete()
    return ', '.join(detected)


@plugin.register(chain='postprocess', requires=['ping'])
def software(ip, **kwargs):
    ip = str(ip)
    try:
        ipaddr = IPAddress.objects.select_related().get(address=ip)
    except IPAddress.DoesNotExist:
        return False, 'no device.', kwargs
    if ipaddr.is_management:
        return False, 'management.', kwargs
    dev = ipaddr.device
    if dev is None:
        return False, 'no device.', kwargs
    name = _detect_software(ip, dev, kwargs.get('http_family', ''))
    return True, name, kwargs
