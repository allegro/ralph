#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
from functools import partial
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.discovery.tasks import run_chain
from ralph.integration import zabbix


class Command(BaseCommand):
    """Register devices in Zabbix and update their templates"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True
    option_list = BaseCommand.option_list + (
            make_option('--remote',
                action='store_true',
                dest='remote',
                default=False,
                help='Run the command on remote workers'
        ),
    )

    def handle(self, *args, **options):
        if options['remote']:
            run = run_chain.delay
        else:
            run = partial(run_chain, interactive=True, clear_down=False)
        context = options
        run(context, 'zabbix')
