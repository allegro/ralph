#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from optparse import make_option
import textwrap

from django.core.management.base import BaseCommand


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
                 'the message queue.',
        ),
        make_option(
            '--plugins',
            dest='plugins',
            default=None,
            help='Run only the selected plugins.',
        ),
        make_option(
            '--dc',
            dest='dc',
            default=None,
            help='Run only on networks from selected data center.',
        ),
        make_option(
            '--queues',
            dest='queues',
            default=None,
            help='Run only on networks on the specified queues.',
        ),
    )

    requires_model_validation = False

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing.
        """
