# -*- coding: utf-8 -*-
import logging
from contextlib import ExitStack
from functools import wraps

import pyhermes
from django.core.exceptions import ValidationError
from django.db import OperationalError, transaction

from ralph.assets.models.assets import ServiceEnvironment
from ralph.data_center.models import (
    Cluster,
    ClusterType,
    VIP,
    VIPProtocol,
)
from ralph.networks.models.networks import IPAddress
from ralph.ralph2_sync.helpers import WithSignalDisabled

logger = logging.getLogger(__name__)


def _get_publisher_signal_info(func):
    """
    Return signal info for publisher in format accepted by `WithSignalDisabled`.
    """
    return {
        'dispatch_uid': func._signal_dispatch_uid,
        'sender': func._signal_model,
        'signal': func._signal_type,
        'receiver': func,
    }


# XXX remove/rename stuff related to ralph2 sync
class sync_subscriber(pyhermes.subscriber):
    """
    Log additional exception when sync has failed.
    """
    def __init__(self, topic, disable_publishers=None):
        self.disable_publishers = disable_publishers or []
        super().__init__(topic)

    def _get_wrapper(self, func):
        @wraps(func)
        @transaction.atomic
        def exception_wrapper(*args, **kwargs):
            # disable selected publisher signals during handling subcriber
            with ExitStack() as stack:
                for publisher in self.disable_publishers:
                    stack.enter_context(WithSignalDisabled(
                        **_get_publisher_signal_info(publisher)
                    ))
                try:
                    return func(*args, **kwargs)
                except (OperationalError, ) as e:
                    logger.exception(
                        'Exception during syncing: {}'.format(str(e))
                    )
                    raise  # return 500 to retry on hermes
                except Exception as e:
                    logger.exception(
                        'Exception during syncing {}'.format(str(e))
                    )
        return exception_wrapper


def validate_event_data(data):
    name = data['name']
    ip = data['ip']
    port = data['port']
    protocol = data['protocol']
    service = data['service']
    if service:
        service_uid = service.get('uid')
    else:
        service_uid = None
    environment = data['environment']
    errors = []

    if not name:
        err = 'missing name'
        errors.append(err)
    try:
        IPAddress(address=ip).clean_fields()
    except (TypeError, ValidationError):
        err = 'invalid IP address "{}"'.format(ip)
        errors.append(err)
    if not port or port < 1024 or port > 49151:
        err = 'invalid port "{}"'.format(port)
        errors.append(err)
    if not protocol:
        err = 'missing name'
        errors.append(err)
    if not service_uid:
        err = 'missing service UID'
        errors.append(err)
    if not environment:
        err = 'missing environment'
        errors.append(err)
    return errors


@sync_subscriber(
    topic='createVipEvent',
)
def handle_create_vip_event(data):
    errors = validate_event_data(data)
    if errors:
        msg = 'Error(s) detected in event data: {}. Ignoring received event.'
        logger.error(msg.format('; '.join(errors)))
        return

    ip, _ = IPAddress.objects.get_or_create(address=data['ip'])
    protocol = getattr(
        VIPProtocol, data['protocol'].upper(), VIPProtocol.unknown
    )
    if VIP.objects.filter(
            ip=ip,
            port=data['port'],
            protocol=protocol,
    ).exists():
        msg = ('VIP designated by IP address {}, port {} and protocol {} '
               'already exists. Ignoring received event.')
        logger.warning(msg.format(ip.address, data['port'], protocol.name))
        return
    cluster_type, _ = ClusterType.objects.get_or_create(
        name=data['load_balancer_type']
    )
    cluster, _ = Cluster.objects.get_or_create(
        name=data['load_balancer'],
        type=cluster_type,
    )
    try:
        service_env = ServiceEnvironment.objects.get(
            service__uid=data['service']['uid'],
            environment__name=data['environment'],
        )
    except ServiceEnvironment.DoesNotExist:
        msg = ('ServiceEnvironment for service UID "{}" and environment "{}" '
               'does not exist. Ignoring received event.')
        logger.error(msg.format(data['service']['uid'], data['environment']))
        return
    vip = VIP(
        name = data['name'],
        ip = ip,
        port = data['port'],
        protocol = protocol,
        parent = cluster,
        service_env = service_env,
    )
    vip.save()
    logger.debug('VIP {} created successfully.'.format(vip.name))


@sync_subscriber(
    topic='deleteVipEvent',
)
def handle_delete_vip_event(data):
    errors = validate_event_data(data)
    if errors:
        msg = 'Error(s) detected in event data: {}. Ignoring received event.'
        logger.error(msg.format('; '.join(errors)))
        return

    # if VIP.objects.filter(
    #         ip=ip,
    #         port=data['port'],
    #         protocol=protocol,
    # ).exists():


@sync_subscriber(
    topic='updateVipEvent',
)
def handle_update_vip_event(data):
    errors = validate_event_data(data)
    if errors:
        msg = 'Error(s) detected in event data: {}. Ignoring received event.'
        logger.error(msg.format('; '.join(errors)))
        return

    # if VIP.objects.filter(
    #         ip=ip,
    #         port=data['port'],
    #         protocol=protocol,
    # ).exists():


@sync_subscriber(
    topic='refreshVipEvent',
)
def handle_refresh_vip_event(data):
    pass
