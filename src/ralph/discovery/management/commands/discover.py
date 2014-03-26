#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from optparse import make_option
from functools import partial
import sys
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand
from ipaddr import IPNetwork

from ralph.discovery.models import Network, Environment
from ralph.discovery.tasks import (
    discover_address,
    discover_all,
    discover_network,
    NoQueueError,
)
from ralph.util import network, plugin


DISCOVERY_DISABLED = getattr(settings, 'DISCOVERY_DISABLED', False)


class OptionBag(object):
    pass


class Command(BaseCommand):

    """Runs discovery of machines in the network. Accepts an optional list
    of network addresses, network names (as defined in the database) or
    host IP addresses. The addresses given do not have to be present in the
    database. If run without arguments, performs full discovery based on the
    configuration from the database.
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '--remote',
            action='store_true',
            dest='remote',
            default=False,
            help='Run the discovery on remote workers by scheduling it on '
                 'the message queue.'),
        make_option(
            '--plugins',
            dest='plugins',
            default=None,
            help='Run only the selected plugins. Works only in interactive'
                 ' mode.'),
        make_option(
            '--dc',
            dest='dc',
            default=None,
            help='Run only the discovery on networks from selected data '
                 'center.'),
        make_option(
            '--env',
            dest='environments',
            default=None,
            help='Run only the discovery on networks from selected '
                 'environment.',
        ),
        make_option(
            '--queues',
            dest='queues',
            default=None,
            help='Run only the discovery on networks on the specified '
                 'queues.'),
    )

    requires_model_validation = False

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing using the queue."""
        if DISCOVERY_DISABLED:
            print(
                'Discovery command is deprecated since Ralph 2.0. '
                'Use ralph scan [arguments] instead.',
            )
            sys.exit()
        interactive = not options['remote']
        discover = OptionBag()
        discover.all = partial(discover_all, interactive=interactive)
        discover.network = partial(discover_network, interactive=interactive)
        discover.single = partial(discover_address, interactive=interactive)
        if options['plugins']:
            if not interactive:
                print(
                    'Limiting plugins not supported on remote execution.',
                    file=sys.stderr,
                )
                sys.exit(2)
            plugin.purge(set(options['plugins'].split(',')))
        self._handle(*args, discover=discover, **options)

    def _handle(self, *args, **options):
        """Actual handling of the request."""
        args = list(args)
        discover = options['discover']
        new_networks = set()
        if options['dc']:
            for dc in options['dc'].split(','):
                dc = dc.strip()
                new_networks.update(n.address for n in Network.objects.filter(
                    data_center__name__iexact=dc))
        if options['queues']:
            for queue in options['queues'].split(','):
                queue = queue.strip()
                for environment in Environment.objects.filter(
                    queue__name__iexact=queue,
                ):
                    new_networks.update(
                        net.address
                        for net in environment.network_set.all(),
                    )
        if options['environments']:
            for environment_name in options['environments'].split(','):
                environment_name = environment_name.strip()
                try:
                    environment = Environment.objects.get(
                        name__iexact=environment_name,
                        queue__isnull=False,
                    )
                except Environment.DoesNotExist:
                    print(
                        "Environment %s does not have configured queue." % (
                            environment_name,
                        ),
                        file=sys.stderr,
                    )
                    sys.exit(2)
                else:
                    new_networks.update(
                        net.address
                        for net in environment.network_set.all(),
                    )
        if new_networks:
            args.extend(new_networks)
        if not args:
            discover.all()
            return
        error = False
        for arg in args:
            try:
                addr = IPNetwork(arg)
            except ValueError:
                try:
                    discover.network(arg)
                except Network.DoesNotExist:
                    ip = network.hostname(arg, reverse=True)
                    if ip:
                        try:
                            discover.single(ip)
                        except NoQueueError as e:
                            print(e)
                    else:
                        print('Hostname or network unknown:', arg)
                        error = True
            else:
                if addr.numhosts > 1:
                    discover.network(addr)
                else:
                    discover.single(addr.ip)
        print()
        if error:
            sys.exit(2)
