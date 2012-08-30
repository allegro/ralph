from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from ralph.cmdb.integration.issuetracker_plugins.jira import JiraAcceptance


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Checking jira tickets acceptance for deployment."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def __init__(self, *args, **kwargs):
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        self.option_list.append(make_option('--cmdb_acceptance_pool',
                dest="cmdb_acceptance_pool",
                action="store_true",
                default=False
            ))

        self.option_list.append(make_option('--run',
            dest="run",
            action="store_true",
            help="Runs syncing",
            default=False
        ))

    def handle(self, *args, **options):
        if options.get('run'):
            logger.debug('Checking bugtracker accepted tickets.')
            j = JiraAcceptance()
            j.run()
            logger.debug('Finished.')
        else:
            print('Please specify option. ')

