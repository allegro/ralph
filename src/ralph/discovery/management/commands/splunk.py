#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import date
from optparse import make_option
import textwrap
import time

from django.core.management.base import BaseCommand

from ralph.discovery.models import (IPAddress, SplunkUsage,
    ComponentModel, ComponentType)
from ralph.util.splunk import Splunk


class Command(BaseCommand):
    """Update billing data from Splunk"""

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
            make_option('--verbose',
                action='store_true',
                dest='verbose',
                default=False,
                help='Verbose progress information.'),)
    requires_model_validation = True

    def handle(self, *args, **options):
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
