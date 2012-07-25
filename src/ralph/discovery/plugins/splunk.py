#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import date
import time

from ralph.discovery.models import (IPAddress, SplunkUsage,
    ComponentModel, ComponentType)
from ralph.discovery.splunk import Splunk
from ralph.util import plugin


@plugin.register(chain='splunk')
def splunk(**options):
    splunk = Splunk()
    splunk.start()
    percent = splunk.progress
    while percent < 100:
        if options['verbose']:
            print(percent)
        time.sleep(30)
        percent = splunk.progress
    hosts = {}
    total_mb = 0
    for item in splunk.results:
        host = item['host']
        mb = float(item['MBytes'])
        total_mb += mb
        if host in hosts:
            hosts[host] += mb
        else:
            hosts[host] = mb
    if options['verbose']:
        print(len(hosts), 'hosts used', total_mb, ' MiBs total.')
    for host, usage in hosts.iteritems():
        ip = IPAddress.objects.filter(hostname__startswith=host).order_by(
            '-last_seen')
        if not ip.count():
            if options['verbose']:
                print('Warning: host', host, 'not found in device database.')
            continue
        dev = ip[0].device
        if not dev:
            if options['verbose']:
                print('Warning: host', host, 'not tied to a device in the '
                    'database.')
            continue
        name = 'Splunk Volume 100 GiB'
        symbol = 'splunkvolume'
        model, created = ComponentModel.concurrent_get_or_create(
                type=ComponentType.unknown.id,
                speed=0, cores=0, size=0, family=symbol, extra_hash=''
            )
        if created:
            model.name = name
            model.save()
        res, created = SplunkUsage.concurrent_get_or_create(
                model=model, device=dev, day=date.today())
        res.size = usage
        res.save()
    return True, 'done.', options
