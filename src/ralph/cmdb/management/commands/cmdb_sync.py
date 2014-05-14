from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import logging

from django.core.management.base import BaseCommand
from optparse import make_option
from ralph.cmdb.importer import CIImporter
from django.contrib.contenttypes.models import ContentType


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    """
    CMDB asset synchronization and  maintanance app.
    Should be run once per day, to update CI from Ralph assets DB
    """
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def __init__(self, *args, **kwargs):
        self.content_types = [
            ContentType.objects.get(app_label='discovery', model='device'),
            ContentType.objects.get(app_label='business', model='venture'),
            ContentType.objects.get(app_label='business', model='venturerole'),
            ContentType.objects.get(app_label='discovery', model='datacenter'),
            ContentType.objects.get(app_label='discovery', model='network'),
            # not used as for now.
            # ContentType.objects.get(app_label='discovery',
            # model='networkterminator'),
        ]
        self.actions = ['purge', 'import']
        self.kinds = [
            'ci', 'user-relations', 'all-relations', 'system-relations'
        ]
        self.option_list = []
        self.option_list.extend(BaseCommand.option_list)
        self.option_list.extend([
            make_option(
                '--action', dest='action', help="Purge all CI and Relations."
            ),
            make_option(
                '--kind', dest='kind', help="Choose import kind.",
            ),
            make_option(
                '--ids', dest='ids',
                help="Choose ids to import.",
            ),
            make_option(
                '--content-types', dest='content_types',
                help="Type of content to reimport.",
                default=[],
            )
        ])
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        usage = "usage: %prog --action=[purge|import] \
            --kind=[ci/user-relations/all-relations/system-relations] \
            --content-types"
        if not options.get('action') or options.get(
                'action') not in self.actions:
            print(usage)
            print("Specify valid action: " + ','.join(self.actions))
            return
        if not options.get('kind') or options.get('kind') not in self.kinds:
            print(usage)
            print("You must specify valid kind: " + '|'.join(self.kinds))
            return
        content_types_names = dict(
            [(x.app_label + '.' + x.model, x) for x in self.content_types])
        content_types_to_import = []
        id_to_import = None
        if options.get('ids'):
            id_to_import = int(options.get('ids'))
        if options.get('content_types'):
            t = options.get('content_types').split(',')
            for ct in t:
                if not content_types_names.get(ct, None):
                    print("Invalid content type: %s: " % ct)
                    return
                else:
                    content_types_to_import.append(
                        content_types_names.get(ct, None))
        else:
            content_types_to_import = self.content_types
        cimp = CIImporter()
        if options.get('action') == 'purge':
            if options.get('kind') == 'ci':
                cimp.purge_all_ci(content_types_to_import)
            elif options.get('kind') == 'all-relations':
                cimp.purge_all_relations()
            elif options.get('kind') == 'user-relations':
                cimp.purge_user_relations()
            elif options.get('kind') == 'system-relations':
                cimp.purge_system_relations()
        elif options.get('action') == 'import':
            if options.get('kind') == 'ci':
                cimp.import_all_ci(content_types_to_import, id_to_import)
            elif options.get('kind') == 'all-relations':
                for content_type in content_types_to_import:
                    cimp.import_relations(content_type, id_to_import)
            else:
                print("Invalid kind for this action")
                return
        logger.info('Ready.')
