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
    Environment,
    Network,
)
from ralph.scan.errors import Error
from ralph.scan.manual import (
    queue_scan_address,
    queue_scan_environment,
    queue_scan_network,
)
from ralph.scan.util import find_network


def print_job_messages(job, last_message, verbose):
    messages = job.meta.get('messages', [])
    for address, plugin, status, message in messages[last_message:]:
        if verbose:
            print('%s %s %s' % (plugin, status, message))
        else:
            if status == 'info' and ('Running plugin' in message):
                print('\nScanning using plugin: %s' % (
                    plugin.split('.')[-1],
                ), file=sys.stderr,
                    end='',
                )
            elif status == 'warning':
                print(' x', file=sys.stderr, end='')
    return len(messages)


class Command(BaseCommand):

    """
    Runs a manual scan of an address, a network of addresses or all networks
    in an environment or data center.
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
            '-e',
            '--environments',
            dest='environment',
            action='store_true',
            default=False,
            help='Scan all networks in the specified environments (space '
                 'delimited).',
        ),
        make_option(
            '-q',
            '--queues',
            dest='queue',
            action='store_true',
            default=False,
            help='Scan all environments that use the specified worker queues ('
                 'space delimited).',
        ),
        make_option(
            '-V',
            '--verbose',
            dest='verbose',
            default=False,
            help='verbose'
        )
    )
    requires_model_validation = False

    def handle(self, *args, **kwargs):
        options_sum = sum([
            kwargs['network'],
            kwargs['data_center'],
            kwargs['environment'],
            kwargs['queue'],
        ])
        if options_sum > 1:
            raise SystemExit(
                "You can't mix networks, environments, data centers and "
                "queues.",
            )
        if not args and options_sum == 0:
            raise SystemExit("Please specify the IP address to scan.")
        plugins = getattr(settings, 'SCAN_PLUGINS', {}).keys()
        verbose = kwargs['verbose']
        if kwargs["plugins"]:
            new_plugins = map(
                lambda s: 'ralph.scan.plugins.{}'.format(s),
                kwargs["plugins"].split(","),
            )
            plugins = filter(lambda plug: plug in new_plugins, plugins)
        if kwargs['network']:
            try:
                for network in [
                    find_network(network_spec) for network_spec in args
                ]:
                    queue_scan_network(network, plugins)
            except (Error, Network.DoesNotExist) as e:
                raise SystemExit(e)
        elif kwargs['environment']:
            try:
                for environment in [
                    Environment.objects.get(name=name) for name in args
                ]:
                    queue_scan_environment(environment, plugins)
            except (Error, Environment.DoesNotExist) as e:
                raise SystemExit(e)
        elif kwargs['data_center']:
            try:
                for data_center in [
                    DataCenter.objects.get(name=name) for name in args
                ]:
                    for environment in data_center.environment_set.filter(
                        queue__isnull=False,
                    ):
                        queue_scan_environment(environment, plugins)
            except (Error, DataCenter.DoesNotExist) as e:
                raise SystemExit(e)
        elif kwargs['queue']:
            try:
                for queue in [
                    DiscoveryQueue.objects.get(name=name) for name in args
                ]:
                    for environment in queue.environment_set.all():
                        queue_scan_environment(environment, plugins)
            except (Error, DiscoveryQueue.DoesNotExist) as e:
                raise SystemExit(e)
        else:
            try:
                ip_addresses = [unicode(ipaddr.IPAddress(ip)) for ip in args]
            except ValueError as e:
                raise SystemExit(e)
            else:
                last_message = 0
                for ip_address in ip_addresses:
                    job = queue_scan_address(ip_address, plugins)
                    while not job.is_finished:
                        job.refresh()
                        last_message = print_job_messages(
                            job, last_message, verbose)
                        if job.is_failed:
                            raise SystemExit(job.exc_info)
                        time.sleep(1)
                    print('\nAll done!')
                    for plugin_name, job_result in job.result.iteritems():
                        if job_result.get('status') == 'success':
                            if not verbose:
                                print('Success: ', plugin_name)
                            else:
                                print('-' * 40)
                                print('Successful plugin: ' + plugin_name)
                                print('Result data:')
                                pprint.pprint(job_result.get('device', ''))
