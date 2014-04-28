from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import logging
import textwrap

from django.core.management.base import BaseCommand
from ralph.util import plugin
from optparse import make_option
from ralph.discovery.tasks import run_chain


logger = logging.getLogger(__name__)


def get_cmdb_plugins():
    for key in plugin.BY_NAME:
        if key.startswith('cmdb'):
            yield key


class Command(BaseCommand):

    """Integration with 3rd party services."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def __init__(self, *args, **kwargs):
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        for plugin_name in get_cmdb_plugins():
            self.option_list.append(make_option(
                '--%s' % plugin_name,
                dest="%s" % plugin_name,
                action="store_true",
                help="Trigger %s plugin" % plugin_name,
                default=False,
            ))
        self.option_list.append(make_option(
            '--remote',
            dest="remote",
            action="store_true",
            help="Runs on remote worker",
            default=False
        ))
        self.option_list.append(make_option(
            '-d',
            '--days',
            dest="days",
            type=int,
            help="Number of days from now back to be checked",
            default=None
        ))

    def handle(self, *args, **options):
        specified_option = False
        interactive = not options['remote']
        cutoff_date = (
            options['days'] and
            datetime.datetime.now() - datetime.timedelta(days=options['days'])
        )
        for chain_name in get_cmdb_plugins():
            if not options.get(chain_name):
                continue
            logger.debug('Executing %s chain .' % chain_name)
            run_chain(
                {'queue': chain_name, 'cutoff_date': cutoff_date},
                chain_name,
                interactive=interactive,
            )
            logger.debug('Finished executing %s chain.' % chain_name)
            specified_option = True
        if not specified_option:
            print('Please specify option. ')


# hook plugins
import ralph.cmdb.integration.sync   # noqa
