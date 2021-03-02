# -*- coding: utf-8 -*-
import logging

import pyhermes
from django.core.exceptions import ValidationError
from django.db import transaction

from ralph.assets.models.assets import ServiceEnvironment
from ralph.data_center.models import Cluster, ClusterType, VIP, VIPProtocol
from ralph.networks.models.networks import Ethernet, IPAddress

logger = logging.getLogger(__name__)


def validate_vip_event_data(data):
    """Performs some basic sanity checks (e.g. missing values) on the incoming
    event data. Returns list of errors (if any).
    """
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
    if not port or port < 0 or port > 65535:
        err = 'invalid port "{}"'.format(port)
        errors.append(err)
    if not protocol:
        err = 'missing protocol'
        errors.append(err)
    if not service_uid:
        err = 'missing service UID'
        errors.append(err)
    if not environment:
        err = 'missing environment'
        errors.append(err)
    return errors


def get_vip(ip, port, protocol):
    try:
        # There should be *at most* one such VIP.
        return VIP.objects.get(ip=ip, port=port, protocol=protocol)
    except VIP.DoesNotExist:
        return None


@pyhermes.subscriber(
    topic='createVipEvent',
)
def handle_create_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = (
            'Error(s) detected in event data: {}. Ignoring received create '
            'event.'
        )
        logger.error(msg.format('; '.join(errors)))
        return

    # Check if VIP already exists.
    ip, ip_created = IPAddress.objects.get_or_create(address=data['ip'])
    protocol = VIPProtocol.from_name(data['protocol'].upper())
    vip = get_vip(ip, data['port'], protocol)
    if vip:
        msg = (
            'VIP designated by IP address {}, port {} and protocol {} '
            'already exists. Ignoring received event.'
        )
        logger.warning(msg.format(ip.address, data['port'], protocol.name))
        return

    # Create it.
    cluster_type, _ = ClusterType.objects.get_or_create(
        name=data['load_balancer_type']
    )
    cluster, _ = Cluster.objects.get_or_create(
        name=data['load_balancer'],
        type=cluster_type,
    )
    if ip_created:
        eth = Ethernet.objects.create(base_object=cluster)
        ip.ethernet = eth
        ip.save()
    try:
        service_env = ServiceEnvironment.objects.get(
            service__uid=data['service']['uid'],
            environment__name=data['environment'],
        )
    except ServiceEnvironment.DoesNotExist:
        msg = (
            'ServiceEnvironment for service UID "{}" and environment "{}" '
            'does not exist. Ignoring received create event.'
        )
        logger.error(msg.format(data['service']['uid'], data['environment']))
        return
    vip = VIP(
        name=data['name'],
        ip=ip,
        port=data['port'],
        protocol=protocol,
        parent=cluster,
        service_env=service_env,
    )
    vip.save()
    logger.debug('VIP {} created successfully.'.format(vip.name))


@pyhermes.subscriber(
    topic='updateVipEvent',
)
def handle_update_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = (
            'Error(s) detected in event data: {}. Ignoring received update '
            'event.'
        )
        logger.error(msg.format('; '.join(errors)))
        return

    ip, _ = IPAddress.objects.get_or_create(address=data['ip'])
    protocol = VIPProtocol.from_name(data['protocol'].upper())
    vip = get_vip(ip, data['port'], protocol)
    if vip is None:
        # VIP not found, should create new one.
        return handle_create_vip_event(data)
    
    # update cluster.
    cluster_type, _ = ClusterType.objects.get_or_create(
        name=data['load_balancer_type']
    )
    cluster, _ = Cluster.objects.get_or_create(
        name=data['load_balancer'],
        type=cluster_type,
    )

    if ip.ethernet.base_object != cluster:
        with transaction.atomic():
            for migrated_vip in VIP.objects.select_for_update().filter(ip=ip):
                migrated_vip.ip.ethernet.base_object = cluster
                migrated_vip.ip.ethernet.save()
                logger.debug('VIP {} with IP {} changed cluster to {}.', migrated_vip.name, ip, cluster.name)
    
    # update service/environment if changed.
    try:
        service_env = ServiceEnvironment.objects.get(
            service__uid=data['service']['uid'],
            environment__name=data['environment'],
        )
    except ServiceEnvironment.DoesNotExist:
        msg = (
            'ServiceEnvironment for service UID "{}" and environment "{}" '
            'does not exist. Ignoring received update event.'
        )
        logger.error(msg.format(data['service']['uid'], data['environment']))
        return
    
    if vip.service_env != service_env:
        vip.service_env = service_env
        vip.save()
        logger.debug('VIP {} changed service/env to {}.'.format(vip.name, service_env))
    
    logger.debug('VIP {} update processed successfuly.'.format(vip.name))


@pyhermes.subscriber(
    topic='deleteVipEvent',
)
def handle_delete_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = (
            'Error(s) detected in event data: {}. Ignoring received delete '
            'event.'
        )
        logger.error(msg.format('; '.join(errors)))
        return

    try:
        ip = IPAddress.objects.get(address=data['ip'])
    except IPAddress.DoesNotExist:
        msg = (
            "IP address {} doesn't exist. Ignoring received delete VIP event."
        )
        logger.error(msg.format(data['ip']))
        return
    protocol = VIPProtocol.from_name(data['protocol'].upper())
    vip = get_vip(ip, data['port'], protocol)
    if vip is None:
        msg = (
            "VIP designated by IP address {}, port {} and protocol {} "
            "doesn't exist. Ignoring received delete event."
        )
        logger.warning(msg.format(ip.address, data['port'], protocol.name))
        return
    vip.delete()
    logger.info('VIP {} deleted successfully.'.format(vip.name))

    # Delete IP address associated with it (along with its Ethernet), but only
    # when this IP is not used anymore by other VIP(s).
    if not VIP.objects.filter(ip=ip).exists():
        eth_deleted = False
        if ip.ethernet is not None:
            ip.ethernet.delete()
            eth_deleted = True
        ip.delete()
        if eth_deleted:
            msg = (
                'IP address {} has been deleted (along with Ethernet '
                'associated with it) since it is no longer being used by any '
                'VIP.'
            )
        else:
            msg = (
                'IP address {} has been deleted since it is no longer being '
                'used by any VIP.'
            )
        logger.info(msg.format(ip.address))
