#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import textwrap
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.business.models import VentureRole
from ralph.discovery.tasks import run_chain
from ralph.integration.models import IntegrationType


class Command(BaseCommand):

    """Register devices in Zabbix and update their templates"""

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
        options['queue'] = 'zabbix'
        role_ids = VentureRole.objects.filter(
            roleintegration__type=IntegrationType.zabbix
        ).exclude(device=None).values_list('id', flat=True)
        if not role_ids:
            print('No venture roles configured for Zabbix integration.',
                  file=sys.stderr)
            sys.exit(1)
        for role_id in role_ids:
            run_chain(
                {'uid': role_id}, 'zabbix', interactive=interactive,
            )
