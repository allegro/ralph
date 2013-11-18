#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pprint
import sys
import textwrap
import time

from optparse import make_option

import ipaddr

from django.conf import settings
from django.core.management.base import BaseCommand

from ralph.discovery.models import (
    DataCenter,
    DiscoveryQueue,
    IPAddress,
    Network,
)
from ralph.scan.errors import Error
from ralph.scan.manual import (
    scan_address,
    scan_data_center,
    scan_network,
)
from ralph.scan.util import find_network


def print_job_messages(job, last_message):
    messages = job.meta.get('messages', [])
    for address, plugin, status, message in messages[last_message:]:
        print('%s(%s): %s' % (plugin, address, message), file=sys.stderr)
    return len(messages)


class Command(BaseCommand):
    """
    Runs a manual scan of an address, a network of addresses or all networks
    in a data center.
    """

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '--plugins',
            dest='plugins',
            default=None,
            help='Run only the selected plugins.',
        ),
        make_option(
            '-n',
            '--networks',
            dest='network',
            action='store_true',
            default=False,
            help='Scan the specified networks (space delimited).',
        ),
        make_option(
            '-c',
            '--data-centers',
            dest='data_center',
            action='store_true',
            default=False,
            help='Scan all networks in the specified data centers (space '
                 'delimited).',
        ),
        make_option(
            '-q',
            '--queues',
            dest='queue',
            action='store_true',
            default=False,
            help='Scan all networks that use the specified worker queues ('
                 'space delimited).',
        ),
    )
    requires_model_validation = False

    def handle(self, *args, **kwargs):
        options_sum = sum([
            kwargs['network'],
            kwargs['data_center'],
            kwargs['queue'],
        ])
        if options_sum > 1:
            raise SystemExit(
                "You can't mix networks, data centers and queues.",
            )
        if not args and options_sum == 0:
            raise SystemExit("Please specify the IP address to scan.")
        plugins = getattr(settings, 'SCAN_PLUGINS', {}).keys()
        if kwargs["plugins"]:
            new_plugins = map(lambda s: 'ralph.scan.plugins.{}'.format(s),
                kwargs["plugins"].split(","),
            )
            plugins = filter(lambda plug: plug in new_plugins, plugins)
        if kwargs['network']:
            try:
                networks = [
                    find_network(network_spec) for network_spec in args
                ]
            except (Error, Network.DoesNotExist) as e:
                raise SystemExit(e)
            else:
                for network in networks:
                    scan_network(network, plugins)
        elif kwargs['data_center']:
            try:
                data_centers = [
                    DataCenter.objects.get(name=name) for name in args
                ]
            except (Error, DataCenter.DoesNotExist) as e:
                raise SystemExit(e)
            else:
                for data_center in data_centers:
                    scan_data_center(data_center, plugins)
        elif kwargs['queue']:
            try:
                queues = [
                    DiscoveryQueue.objects.get(name=name) for name in args
                ]
            except (Error, DiscoveryQueue.DoesNotExist) as e:
                raise SystemExit(e)
            else:
                for queue in queues:
                    for network in queue.network_set.all():
                        scan_network(network, plugins)
        else:
            try:
                addresses = [unicode(ipaddr.IPAddress(ip)) for ip in args]
            except ValueError as e:
                raise SystemExit(e)
            else:
                last_message = 0
                for address in addresses:
                    ip_address, created = IPAddress.concurrent_get_or_create(
                        address=address,
                    )
                    job = scan_address(ip_address, plugins)
                    while not job.is_finished:
                        job.refresh()
                        print(
                            'Progress: %d/%d plugins' % (
                                len(job.meta.get('finished', [])),
                                len(plugins),
                            ),
                        )
                        last_message = print_job_messages(job, last_message)
                        if job.is_failed:
                            raise SystemExit(job.exc_info)
                        time.sleep(5)
                    last_message = print_job_messages(job, last_message)
                    pprint.pprint(job.result)

