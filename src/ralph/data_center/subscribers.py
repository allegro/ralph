# -*- coding: utf-8 -*-
import logging

import pyhermes
from django.contrib.contenttypes.models import ContentType
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
    name = data["name"]
    ip = data["ip"]
    port = data["port"]
    protocol = data["protocol"]
    service = data["service"]
    if service:
        service_uid = service.get("uid")
    else:
        service_uid = None
    environment = data["environment"]
    errors = []

    if not name:
        err = "missing name"
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
        err = "missing protocol"
        errors.append(err)
    if not service_uid:
        err = "missing service UID"
        errors.append(err)
    if not environment:
        err = "missing environment"
        errors.append(err)
    return errors


def get_vip(ip, port, protocol):
    try:
        # There should be *at most* one such VIP.
        return VIP.objects.get(ip=ip, port=port, protocol=protocol)
    except VIP.DoesNotExist:
        return None


@pyhermes.subscriber(
    topic="createVipEvent",
)
def handle_create_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = "Error(s) detected in event data: %s. Ignoring received create " "event."
        logger.error(msg, "; ".join(errors))
        return

    # Check if VIP already exists.
    ip, ip_created = IPAddress.objects.get_or_create(address=data["ip"])
    protocol = VIPProtocol.from_name(data["protocol"].upper())
    vip = get_vip(ip, data["port"], protocol)
    if vip:
        msg = (
            "VIP designated by IP address %s, port %s and protocol %s "
            "already exists. Ignoring received event."
        )
        logger.warning(msg, ip.address, data["port"], protocol.name)
        return

    # Create it.
    cluster_type, _ = ClusterType.objects.get_or_create(name=data["load_balancer_type"])
    cluster, _ = Cluster.objects.get_or_create(
        name=data["load_balancer"],
        type=cluster_type,
    )
    if ip_created:
        eth = Ethernet.objects.create(base_object=cluster)
        ip.ethernet = eth
        ip.save()
    elif ip.dhcp_expose:
        logger.error(
            "Trying to create VIP with IP %s, port %s and protocol %s "
            "failed because IP is exposed in dhcp",
            ip.address,
            data["port"],
            protocol.name,
        )
        return
    try:
        service_env = ServiceEnvironment.objects.get(
            service__uid=data["service"]["uid"],
            environment__name=data["environment"],
        )
    except ServiceEnvironment.DoesNotExist:
        msg = (
            'ServiceEnvironment for service UID "%s" and environment "%s" '
            "does not exist. Ignoring received create event."
        )
        logger.error(msg, data["service"]["uid"], data["environment"])
        return
    vip = VIP(
        name=data["name"],
        ip=ip,
        port=data["port"],
        protocol=protocol,
        parent=cluster,
        service_env=service_env,
    )
    vip.save()
    logger.debug("VIP %s created successfully.", vip.name)


def migrate_vip_to_cluster(vip, cluster, protocol):
    msg = (
        "Trying to update VIP with IP %s, port %s and protocol %s" "failed: %s",
        (vip.ip.address, vip.port, protocol.name),
    )
    cluster_content_type = ContentType.objects.get_for_model(Cluster)
    ethernet = vip.ip.ethernet
    if not ethernet:
        logger.error(msg[0], *msg[1], "no `Ethernet` object found")
        return
    if ethernet.base_object.content_type != cluster_content_type:
        logger.error(
            msg[0], *msg[1], "`Ethernet` base_object is not `Cluster` instance"
        )
        return
    if vip.parent.content_type != cluster_content_type:
        logger.error(msg[0], *msg[1], "`VIP` parent is not `Cluster` instance")
        return

    ethernet.base_object = cluster
    ethernet.save()
    vip.parent = cluster
    vip.save()
    logger.debug(
        "VIP %s with IP %s, port %s and protocol %s changed cluster to %s.",
        vip.name,
        vip.ip.address,
        vip.port,
        protocol.name,
        cluster.name,
    )


@pyhermes.subscriber(
    topic="updateVipEvent",
)
def handle_update_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = "Error(s) detected in event data: %s. Ignoring received update " "event."
        logger.error(msg, "; ".join(errors))
        return

    ip, _ = IPAddress.objects.get_or_create(address=data["ip"])
    protocol = VIPProtocol.from_name(data["protocol"].upper())
    if ip.dhcp_expose:
        logger.error(
            "Trying to update VIP with IP %s, port %s and protocol %s "
            "failed because IP is exposed in dhcp",
            ip.address,
            data["port"],
            protocol.name,
        )
        return

    vip = get_vip(ip, data["port"], protocol)
    if vip is None:
        # VIP not found, should create new one.
        return handle_create_vip_event(data)

    # update cluster.
    cluster_type, _ = ClusterType.objects.get_or_create(name=data["load_balancer_type"])
    cluster, _ = Cluster.objects.get_or_create(
        name=data["load_balancer"],
        type=cluster_type,
    )

    if vip.parent != cluster or (ip.ethernet and ip.ethernet.base_object != cluster):
        with transaction.atomic():
            for migrated_vip in VIP.objects.select_for_update().filter(ip=ip):
                migrate_vip_to_cluster(migrated_vip, cluster, protocol)

    # update service/environment if changed.
    try:
        service_env = ServiceEnvironment.objects.get(
            service__uid=data["service"]["uid"],
            environment__name=data["environment"],
        )
    except ServiceEnvironment.DoesNotExist:
        msg = (
            'ServiceEnvironment for service UID "%s" and environment "%s" '
            "does not exist. Ignoring received update event."
        )
        logger.error(msg, data["service"]["uid"], data["environment"])
        return

    if vip.service_env != service_env:
        vip.service_env = service_env
        vip.save()
        logger.debug("VIP %s changed service/env to %s.", vip.name, service_env)

    logger.debug("VIP %s update processed successfully.", vip.name)


@pyhermes.subscriber(
    topic="deleteVipEvent",
)
def handle_delete_vip_event(data):
    errors = validate_vip_event_data(data)
    if errors:
        msg = "Error(s) detected in event data: %s. Ignoring received delete " "event."
        logger.error(msg, "; ".join(errors))
        return

    try:
        ip = IPAddress.objects.get(address=data["ip"])
    except IPAddress.DoesNotExist:
        msg = "IP address %s doesn't exist. Ignoring received delete VIP event."
        logger.error(msg, data["ip"])
        return
    protocol = VIPProtocol.from_name(data["protocol"].upper())
    vip = get_vip(ip, data["port"], protocol)
    if vip is None:
        msg = (
            "VIP designated by IP address %s, port %s and protocol %s "
            "doesn't exist. Ignoring received delete event."
        )
        logger.warning(msg, ip.address, data["port"], protocol.name)
        return
    vip.delete()
    logger.info("VIP %s deleted successfully.", vip.name)

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
                "IP address %s has been deleted (along with Ethernet "
                "associated with it) since it is no longer being used by any "
                "VIP."
            )
        else:
            msg = (
                "IP address %s has been deleted since it is no longer being "
                "used by any VIP."
            )
        logger.info(msg, ip.address)
