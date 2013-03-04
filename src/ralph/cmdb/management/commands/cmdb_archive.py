#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.cmdb.archiver import (
    run_cichange_git_archivization,
    run_cichange_zabbix_archivization,
    run_cichange_so_archivization,
    run_cichange_cmdb_history_archivization,
    run_cichange_device_archivization,
    run_cichange_puppet_archivization,
)

ACTIONS_TYPES_MAPPER = {
    'git': run_cichange_git_archivization,
    'zabbix': run_cichange_zabbix_archivization,
    'so': run_cichange_so_archivization,
    'cmdb': run_cichange_cmdb_history_archivization,
    'ralph': run_cichange_device_archivization,
    'puppet': run_cichange_puppet_archivization,
}


class Command(BaseCommand):
    help = 'CMDB archivization.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--type',
            dest='type',
            default=False,
            help='Choose archivization type.',
            type='choice',
            choices=ACTIONS_TYPES_MAPPER.keys(),
        ),
    )

    def handle(self, *args, **options):
        action_type = options.get('type')
        if not action_type:
            print(
                'Usage: %prog --type=[{}]'.format(
                    '|'.join(ACTIONS_TYPES_MAPPER.keys()),
                ),
            )
            return
        older_than = datetime.datetime.now() - datetime.timedelta(days=90)
        ACTIONS_TYPES_MAPPER[action_type](older_than)
