#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from optparse import make_option
import textwrap
from functools import partial

from django.core.management.base import BaseCommand

from ralph.discovery.tasks import run_chain



class Command(BaseCommand):
    """Update billing data from Splunk"""

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
            make_option('--verbose',
                action='store_true',
                dest='verbose',
                default=False,
                help='Verbose progress information.'
            ),
            make_option('--remote',
                action='store_true',
                dest='remote',
                default=False,
                help='Run the command on remote workers'
            ),

        )
    requires_model_validation = True

    def handle(self, *args, **options):
        if options['remote']:
            run = run_chain.delay
        else:
            run = partial(run_chain, interactive=True, clear_down=False)
        context = options
        run(context, 'splunk')

