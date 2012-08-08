from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import logging
import re

from django.core.management.base import BaseCommand
from ralph.util import plugin
from functools import partial
from optparse import make_option
from ralph.discovery.tasks import run_chain
# hook plugins
import ralph.cmdb.integration.sync

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Integration with 3rd party services."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def get_cmdb_plugins(self):
        return dict([(x, plugin.BY_NAME[x]) for x in plugin.BY_NAME.keys() if x.startswith('cmdb')])

    def __init__(self, *args, **kwargs):
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        for p in self.get_cmdb_plugins().iteritems():
            plugin_name = p[0]
            self.option_list.append(make_option('--%s' % plugin_name,
                dest="%s" % plugin_name,
                action="store_true",
                help="Trigger %s plugin" % plugin_name,
                default=False
            ))
        self.option_list.append(make_option('--remote',
            dest="remote",
            action="store_true",
            help="Runs on remote worker",
            default=False
        ))

    def handle(self, *args, **options):
        specified_option = False
        if options.get('remote'):
            run = run_chain.delay
        else:
            run = partial(run_chain, interactive=True, clear_down=False)
        context = {'context' : ''}
        for p in self.get_cmdb_plugins().iteritems():
            if options.get(p[0]):
                chain_name=p[0]
                logger.debug('Executing %s chain .' % p[0])
                run(context, chain_name)
                logger.debug('Finished executing %s chain.' % p[0])
                specified_option = True
        if not specified_option:
            print('Please specify option. ')

