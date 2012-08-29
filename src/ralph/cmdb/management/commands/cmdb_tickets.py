from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.util import plugin
from ralph.cmdb import models_changes  as chdb
from ralph.cmdb import models_signals  as signals


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """This tool synchronize database with Jira tickets in case of errors."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def get_cmdb_plugins(self):
        return dict([(x, plugin.BY_NAME[x]) for x in plugin.BY_NAME.keys() if x.startswith('cmdb')])

    def __init__(self, *args, **kwargs):
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        self.option_list.append(make_option('--run',
            dest="run",
            action="store_true",
            help="Runs syncing",
            default=False
        ))

    def handle(self, *args, **options):
        if options.get('run'):
            logger.debug('Syncing tickets.')
            for change in chdb.CIChange.objects.filter(
                    type__in=chdb.REGISTER_CHANGE_TYPES,
                    registration_type=chdb.CI_CHANGE_REGISTRATION_TYPES.NOT_REGISTERED.id):
                logger.debug('Starting task with change id=%d' % change.id)
                signals.getfunc(signals.create_issue)(change.id)

            logger.debug('Finished syncing tickets.')
        else:
            print('Please specify option. ')

