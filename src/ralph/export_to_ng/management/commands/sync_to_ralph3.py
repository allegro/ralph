# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re
from optparse import make_option

from django.core.management.base import BaseCommand

from ralph.business.models import Venture, VentureRole
from ralph.discovery.models import Device
# register handlers
from ralph.export_to_ng import publishers  # noqa

logger = logging.getLogger(__name__)


def generic_sync(model, **options):
    for obj in model._default_manager.all():
        obj.save()


def venture_sync(model, **options):
    """
    Venture sync.

    Handles:
    * skipping empty ventures (ventures without any device attached) when
        --skip-empty is used.
    * syncing in valid order (to property handle parent-child relation).
    """
    skip_empty = options.get('skip_empty')
    valid_ventures = {}
    for v in Venture.objects.all():
        dev_count = Device.admin_objects.filter(
            venture__in=v.find_descendant_ids()
        ).count()
        if (skip_empty and dev_count > 0) or not skip_empty:
            valid_ventures[v] = dev_count
        else:
            logger.warning('Skipping empty venture {}'.format(v))
    # sort by number of assigned devices to properly handle parent-child
    # relation
    ventures = [
        k for k, v in sorted(valid_ventures.items(), key=lambda x: -x[1])
    ]
    for venture in ventures:
        logger.info('Saving {}'.format(venture))
        venture.save()


def venture_role_sync(model, **options):
    """
    VentureRole sync.

    Handles:
    * skipping empty roles (roles without any device attached) when --skip-empty
        is used.
    * skipping roles with invalid name (name is not valid slug).
    """
    for obj in VentureRole._default_manager.all():
        is_empty = obj.device.count() == 0
        # match slug regex for conf. class in Ralph3
        if not re.match(r'^\w+$', obj.name) and not is_empty:
            logger.warning((
                'VentureRole {} name ("{}") is not valid slug It\'s assigned '
                'to {} objects. Skipping..'
            ).format(obj, obj.name, obj.device.count()))
            continue
        if options.get('skip_empty') and is_empty:
            logger.warning('Skipping empty role {}'.format(obj))
            continue
        obj.save()


models_handlers = {
    'Venture': (Venture, venture_sync),
    'VentureRole': (VentureRole, venture_role_sync),
}


class Command(BaseCommand):
    help = "Sync particular model to Ralph3"

    option_list = BaseCommand.option_list + (
        make_option(
            '-m', '--model',
            help='Name of the model to sync',
            choices=list(models_handlers),
            action='append',
            dest='models'
        ),
        make_option(
            '--skip-empty',
            action="store_true",
        ),
    )

    def handle(self, *args, **options):
        for model_name in options.get('models', []):
            model, handler = models_handlers[model_name]
            logger.info('Syncing {}'.format(model_name))
            handler(model, **options)
