#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.discovery.tasks import run_chain


class Command(BaseCommand):

    """Update the billing data from OpenStack"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True
    option_list = BaseCommand.option_list + (
        make_option(
            '--remote',
            action='store_true',
            dest='remote',
            default=False,
            help='Run the command on remote workers',
        ),
    )

    def handle(self, *args, **options):
        interactive = not options['remote']
        run_chain({}, 'openstack', interactive=interactive)
