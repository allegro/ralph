#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from optparse import make_option

import ipaddr

from django.core.management.base import BaseCommand

from ralph.discovery.models import (
    DataCenter,
    DiscoveryQueue,
    Environment,
    Network,
)
from ralph.scan.autoscan import (
    queue_autoscan_address,
    queue_autoscan_environment,
    queue_autoscan_network,
)
from ralph.scan.errors import Error
from ralph.scan.util import find_network


class Command(BaseCommand):

    """
    Runs an automatic pre-scan of an address, a network of addresses or all
    networks in an environment or data center.
    """

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
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
            help='Scan all networks in the specified environment (space '
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
    )
    requires_model_validation = False

    def handle(self, *args, **kwargs):
        if sum([
            kwargs['network'],
            kwargs['data_center'],
            kwargs['environment'],
            kwargs['queue']
        ]) > 1:
            raise SystemExit(
                "You can't mix networks, environments, data centers and "
                "queues.",
            )
        if not args:
            raise SystemExit("Please specify the addresses to scan.")
        if kwargs['network']:
            try:
                for network in [
                    find_network(network_spec) for network_spec in args
                ]:
                    queue_autoscan_network(network)
            except (Error, Network.DoesNotExist) as e:
                raise SystemExit(e)
        elif kwargs['environment']:
            try:
                for environment in [
                    Environment.objects.get(name=name) for name in args
                ]:
                    queue_autoscan_environment(environment)
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
                        queue_autoscan_environment(environment)
            except (Error, DataCenter.DoesNotExist) as e:
                raise SystemExit(e)
        elif kwargs['queue']:
            try:
                for queue in [
                    DiscoveryQueue.objects.get(name=name) for name in args
                ]:
                    for environment in queue.environment_set.all():
                        queue_autoscan_environment(environment)
            except (Error, DiscoveryQueue.DoesNotExist) as e:
                raise SystemExit(e)
        else:
            try:
                addresses = [str(ipaddr.IPAddress(ip)) for ip in args]
                for address in addresses:
                    queue_autoscan_address(address)
            except (Error, ValueError) as e:
                raise SystemExit(e)
