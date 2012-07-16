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

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from ipaddr import IPNetwork

from ralph.discovery.models import Network
from ralph.discovery.tasks import discover_single, discover_network, \
    discover_all
from ralph.util import network, plugin

class OptionBag(object): pass


class Command(BaseCommand):
    """Runs discovery of machines in the network. Accepts an optional list
    of network addresses, network names (as defined in the database) or
    host IP addresses. The addresses given do not have to be present in the
    database. If run without arguments, performs full discovery based on the
    configuration from the database.
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
            make_option('--remote',
                action='store_true',
                dest='remote',
                default=False,
                help='Run the discovery on remote workers by scheduling it on '
                     'the message queue.'),
            make_option('--plugins',
                dest='plugins',
                default=None,
                help='Run only the selected plugins. Works only in interactive'
                     ' mode.'),
            make_option('--dc',
                dest='dc',
                default=None,
                help='Run only the discovery on networks from selected data '
                     'center.'),
            make_option('--queues',
                dest='queues',
                default=None,
                help='Run only the discovery on networks on the specified '
                     'Celery queues.'),
    )

    requires_model_validation = False

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing using Rabbit."""
        discover = OptionBag()
        if options['remote']:
            discover.all = discover_all.delay
            discover.network = discover_network.delay
            discover.single = discover_single.delay
        else:
            if options['plugins']:
                plugin.purge(set(options['plugins'].split(',')))
            discover.all = partial(discover_all, interactive=True)
            discover.network = partial(discover_network, interactive=True)
            discover.single = partial(discover_single, interactive=True,
                clear_down=False)
        try:
            self._handle(*args, discover=discover, **options)
        except ImproperlyConfigured, e:
            print(e.message, file=sys.stderr)
            sys.exit(1)

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
                new_networks.update(n.address for n in Network.objects.filter(
                    queue__iexact=queue))
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
                        discover.single({'ip': ip})
                    else:
                        print('Hostname or network unknown:', arg)
                        error = True
            else:
                if addr.numhosts > 1:
                    discover.network(addr)
                else:
                    discover.single({'ip': addr.ip})
        print()
        if error:
            sys.exit(2)
