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

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Integration with 3rd party services."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def __init__(self, *args, **kwargs):
        required_plugin_name = re.compile('[^-]+')
        cmdb_plugins = plugin.BY_NAME['cmdb'].iteritems()
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        for p in cmdb_plugins:
            plugin_name = p[0]
            if not required_plugin_name.match(plugin_name):
                raise UserWarning("Invalid plugin name: %s " % plugin_name)
            self.option_list.append(make_option('--%s' % plugin_name,
                dest="%s" % plugin_name,
                action="store_true",
                help="Trigger %s plugin" % plugin_name,
                default=False
            ))

    def handle(self, *args, **options):
        cmdb_plugins = plugin.BY_NAME['cmdb'].iteritems()
        specified_option = False
        if options.get('remote'):
            run = run_chain.delay
        else:
            run = partial(run_chain, interactive=True, clear_down=False)
        context = {}
        for p in cmdb_plugins:
            if options.get(p[0]):
                func_name = p[1]
                logger.debug('Executing %s plugin.' % p[0])
                run(context, func_name)
                logger.debug('Finished executing %s plugin.' % p[0])
                specified_option = True
        if not specified_option:
            print('Please specify option. ')

