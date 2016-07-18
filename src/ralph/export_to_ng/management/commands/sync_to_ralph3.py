# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re
import time
import sys
from ipaddr import AddressValueError, IPv4Network
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_save

from ralph.business.models import (
    RoleProperty,
    RolePropertyValue,
    Venture,
    VentureRole
)
from ralph.discovery.models import (
    Device,
    DeviceType,
    Network,
    NetworkKind,
    Environment as NetworkEnvironment
)
# register handlers
from ralph.export_to_ng import publishers  # noqa

logger = logging.getLogger(__name__)


def generic_sync(model, **options):
    for obj in model._default_manager.all():
        post_save.send(
            sender=model,
            instance=obj,
            raw=None,
            using='default',
            _sync_fields=options.get('_sync_fields')
        )
        time.sleep(options['sleep'])


def virtual_server_sync(model, **options):
    for obj in model._default_manager.filter(
        model__type=DeviceType.virtual_server,
        id__in=settings.RALPH2_HERMES_VIRTUAL_SERVERS_IDS_WHITELIST
    ):
        post_save.send(
            sender=model, instance=obj, raw=None, using='default'
        )
        time.sleep(options['sleep'])


def stacked_switch_sync(model, **options):
    for obj in model._default_manager.filter(
        model__type=DeviceType.switch_stack,
        deleted=False,
    ):
        post_save.send(
            sender=model, instance=obj, raw=None, using='default'
        )
        time.sleep(options['sleep'])


def role_property_sync(model, **options):
    for obj in model._default_manager.filter(
        symbol__in=settings.RALPH2_HERMES_ROLE_PROPERTY_WHITELIST
    ):
        obj.save()
        time.sleep(options['sleep'])


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
        descendants = v.find_descendant_ids()
        dev_count = Device.admin_objects.filter(
            venture__in=descendants
        ).exclude(deleted=True).count()
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
        post_save.send(
            sender=Venture, instance=venture, raw=None, using='default'
        )
        time.sleep(options['sleep'])


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
            ).format(obj, obj.name, obj.device.exclude(deleted=True).count()))
            continue
        if options.get('skip_empty') and is_empty:
            logger.warning('Skipping empty role {}'.format(obj))
            continue
        post_save.send(
            sender=VentureRole, instance=obj, raw=None, using='default'
        )
        time.sleep(options['sleep'])


def _device_partial_sync(fields, **options):
    for obj in Device.objects.exclude(deleted=True):
        if (
            options.get('device_with_asset_only') and
            not obj.get_asset(manager='admin_objects')
        ):
            logger.info('Skipping {} - it does not have asset'.format(obj))
            continue
        post_save.send(
            sender=Device,
            instance=obj,
            raw=None,
            using='default',
            _sync_fields=fields
        )
        time.sleep(options['sleep'])


def device_venture_sync(model, **options):
    _device_partial_sync(['id', 'venture_role'], **options)


def device_role_properties_sync(model, **options):
    _device_partial_sync(['id', 'custom_fields'], **options)


def network_sync(model, **options):
    exclude = Q()
    for network in (options.get('exclude_network', []) or []):
        try:
            net = IPv4Network(network)
        except AddressValueError:
            print(
                "Value '{}' for '--exclude-network' is not CIDR format".format(
                    network
                )
            )
            sys.exit(1)
        else:
            exclude |= Q(
                Q(min_ip__gte=int(net.network)) &
                Q(max_ip__lte=int(net.broadcast))
            )
    # order networks by size (largest first)
    for obj in Network.objects.exclude(exclude).order_by('min_ip', '-max_ip'):
        post_save.send(
            sender=model,
            instance=obj,
            raw=None,
            using='default',
        )
        time.sleep(options['sleep'])


models_handlers = {
    'Venture': (Venture, venture_sync),
    'VentureRole': (VentureRole, venture_role_sync),
    'RoleProperty': (RoleProperty, role_property_sync),
    'RolePropertyValue': (RolePropertyValue, generic_sync),
    'Device': (Device, generic_sync),
    'VirtualServer': (Device, virtual_server_sync),
    'StackedSwitch': (Device, stacked_switch_sync),
    'DeviceVentureOnly': (Device, device_venture_sync),
    'DeviceRolePropertiesOnly': (Device, device_role_properties_sync),
    'Network': (Network, network_sync),
    'NetworkKind': (NetworkKind, generic_sync),
    'NetworkEnvironment': (NetworkEnvironment, generic_sync),
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
        make_option(
            '--device-with-asset-only',
            action="store_true",
        ),
        make_option(
            '--sleep',
            type=int,
            default=0,
            help='Sleep time after each sync in seconds'
        ),
        make_option(
            '--exclude-network',
            action="append",
            help='Excludes network from address, eg.: --exclude-network=10.20.30.0/24',  # noqa
            type="str"
        ),
    )

    def handle(self, *args, **options):
        for model_name in options.get('models', []):
            model, handler = models_handlers[model_name]
            logger.info('Syncing {}'.format(model_name))
            handler(model, **options)
