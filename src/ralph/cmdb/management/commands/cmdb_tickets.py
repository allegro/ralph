from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.cmdb import models_changes as chdb
from ralph.cmdb.models_signals import register_issue_signal


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    """This tool synchronize database with Jira tickets in case of errors."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    option_list = BaseCommand.option_list + (
        make_option(
            '--run',
            action='store_true',
            dest='run',
            default=False,
            help='Deprecated. Does nothing.',
        ),
    )

    def handle(self, *args, **options):
        logger.debug('Syncing tickets.')
        for change in chdb.CIChange.objects.filter(
                registration_type=chdb.CI_CHANGE_REGISTRATION_TYPES.WAITING):
            register_issue_signal.send(sender=self, change_id=change.id)
        logger.debug('Finished syncing tickets.')
