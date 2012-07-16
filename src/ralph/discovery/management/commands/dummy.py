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

from ralph.discovery.tasks import dummy_horde


class OptionBag(object): pass


class Command(BaseCommand):
    """Runs a horde of dummy tasks for testing whether the scaffolding works. 
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
            make_option('--remote',
                action='store_true',
                dest='remote',
                default=False,
                help='Run the horde by scheduling it on '
                     'the message queue.'),
            )
    requires_model_validation = False

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing using Rabbit."""
        try:
            how_many = int(args[0])
        except (ValueError, TypeError, IndexError):
            how_many = 1000
        if options['remote']:
            dummy_horde.delay(how_many=how_many, interactive=False)
        else:
            dummy_horde(how_many=how_many, interactive=True)
