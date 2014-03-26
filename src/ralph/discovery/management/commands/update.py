#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Updates already discovered machines."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from ralph.discovery.models import Network
from ralph.discovery.management.commands import discover


class Command(discover.Command):

    """Runs discovery update on existing machines in the network. Accepts an
    optional list of network names (as defined in the database). If run without
    arguments, performs full update based on the configuration from the
    database.
    """

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
                new_networks.update(
                    n.address
                    for n in Network.objects.filter(
                        environment__queue__name__iexact=queue,
                    )
                )
        if new_networks:
            args.extend(new_networks)
        if not args:
            discover.all(update_existing=True)
            return
        try:
            for arg in args:
                try:
                    Network.objects.get(address=arg)
                except Network.DoesNotExist:
                    Network.objects.get(name=arg)
                discover.network(arg, update_existing=True)
        except Network.DoesNotExist:
            print('Network {} is not known.'.format(arg))
            sys.exit(2)
        print()
