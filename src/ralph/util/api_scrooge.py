# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db

from ralph.cmdb.models import CI, CIAttributeValue, CIOwner, CIType
from ralph.discovery.models import (
    Device,
    DeviceEnvironment,
    DeviceType,
    DiskShareMount,
    FibreChannel,
    IPAddress,
)


def get_virtual_usages(parent_service_uid=None):
    """Yields dicts reporting the number of virtual cores, memory and disk."""
    devices = Device.objects.filter(model__type=DeviceType.virtual_server)
    if parent_service_uid:
        devices = devices.filter(
            parent__service__uid=parent_service_uid,
        )
    for device in devices:
        cores = device.get_core_count()
        memory = device.memory_set.aggregate(db.Sum('size'))['size__sum']
        disk = device.storage_set.aggregate(db.Sum('size'))['size__sum']
        shares_size = sum(
            mount.get_size()
            for mount in device.disksharemount_set.all()
        )
        for system in device.operatingsystem_set.all():
            if not disk:
                disk = max((system.storage or 0) - shares_size, 0)
            if not cores:
                cores = system.cores_count
            if not memory:
                memory = system.memory
        yield {
            'name': device.name,
            'device_id': device.id,
            'venture_id': device.venture_id,
            'service_id': device.service_id,
            'environment_id': device.device_environment_id,
            'hypervisor_id': device.parent_id,
            'virtual_cores': cores or 0,
            'virtual_memory': memory or 0,
            'virtual_disk': disk or 0,
        }


def get_shares(service_uid=None, include_virtual=True):
    """
    Yields dicts reporting the storage shares mounts.

    :param service_uid: if passed, only share mounts from shares with
        storage device in this service will be returned
    :param include_virtual: if False, virtual share mounts will be excluded
        from result
    """
    shares_mounts = DiskShareMount.objects.select_related(
        'share',
    )
    if not include_virtual:
        shares_mounts = shares_mounts.filter(is_virtual=False)
    if service_uid:
        shares_mounts = shares_mounts.filter(
            share__device__service__uid=service_uid,
        )
    for mount in shares_mounts:
        yield {
            'storage_device_id': mount.share.device_id,
            'mount_device_id': mount.device_id,
            'label': mount.share.label,
            'size': mount.get_size(),
        }


def get_ip_info(ipaddress):
    """Returns device information by IP address"""
    result = {}
    try:
        ip = IPAddress.objects.select_related().get(address=ipaddress)
    except IPAddress.DoesNotExist:
        pass
    else:
        if ip.venture is not None:
            result['venture_id'] = ip.venture.id
        if ip.device is not None:
            result['device_id'] = ip.device.id
            if ip.device.venture is not None:
                result['venture_id'] = ip.device.venture.id
    return result


def get_ip_addresses(only_public=False):
    """Yileds available IP addresses"""
    ips = IPAddress.objects.filter(is_public=only_public)
    return {ip.address: ip.venture.id if ip.venture else None for ip in ips}


def get_fc_cards():
    for fc in FibreChannel.objects.filter(device__deleted=False).values(
        'id',
        'device_id'
    ):
        yield {
            'id': fc['id'],
            'device_id': fc['device_id'],
        }


def get_environments():
    for environment in DeviceEnvironment.objects.all():
        yield {
            'ci_id': environment.id,
            'ci_uid': environment.uid,
            'name': environment.name,
        }


def get_openstack_tenants():
    for tenant in Device.objects.filter(
        sn__startswith='openstack',
        model__type=DeviceType.cloud_server
    ):
        yield {
            'device_id': tenant.id,
            'tenant_id': tenant.sn[len('openstack-'):],
            'service_id': tenant.service_id,
            'environment_id': tenant.device_environment_id,
            'name': tenant.name,
            'model_id': tenant.model_id,
            'model_name': tenant.model.name,
            'remarks': tenant.remarks,
        }


def get_blade_servers():
    for blade_server in Device.objects.filter(
        model__type=DeviceType.blade_server,
    ):
        yield {
            'device_id': blade_server.id,
        }


# CMDB
def get_business_lines():
    """
    Returns Business Lines from CMDB (CIs with type Business Line)
    """
    business_line_type = CIType.objects.get(name='BusinessLine')
    for business_line in CI.objects.filter(type=business_line_type):
        yield {
            'ci_id': business_line.id,
            'ci_uid': business_line.uid,
            'name': business_line.name,
        }


def get_profit_centers():
    """
    Returns Profit Centers from CMDB (CIs with type Profit Center)
    """
    profit_center_type = CIType.objects.get(name='ProfitCenter')
    business_line_type = CIType.objects.get(name='BusinessLine')
    for profit_center in CI.objects.filter(type=profit_center_type):
        try:
            description = profit_center.ciattributevalue_set.get(
                attribute__name='description'
            ).value
        except CIAttributeValue.DoesNotExist:
            description = None
        business_line = profit_center.child.filter(
            parent__type=business_line_type
        ).values_list('parent__id', flat=True)
        yield {
            'ci_id': profit_center.id,
            'ci_uid': profit_center.uid,
            'name': profit_center.name,
            'description': description,
            'business_line': business_line[0] if business_line else None,
        }


def get_owners():
    """
    Returns CIOwners from CMDB
    """
    for owner in CIOwner.objects.all():
        yield {
            'id': owner.id,
            'profile_id': owner.profile_id,
        }


def get_services():
    """
    Returns Services (CIs with type Service) with additional information like
    owners, business line etc.
    """
    service_type = CIType.objects.get(name='Service')
    profit_center_type = CIType.objects.get(name='ProfitCenter')
    environment_type = CIType.objects.get(name='Environment')
    for service in CI.objects.filter(
        type=service_type
    ).select_related('relations'):
        profit_center = service.child.filter(
            parent__type=profit_center_type
        ).values_list('parent__id', flat=True)
        # TODO: verify relation
        environments = service.parent.filter(
            child__type=environment_type,
        )
        try:
            symbol = service.ciattributevalue_set.get(
                attribute__name='symbol'
            ).value
        except CIAttributeValue.DoesNotExist:
            symbol = None
        yield {
            'ci_id': service.id,
            'ci_uid': service.uid,
            'name': service.name,
            'symbol': symbol,
            'profit_center': profit_center[0] if profit_center else None,
            'business_owners': list(service.business_owners.values_list(
                'id',
                flat=True,
            )),
            'technical_owners': list(service.technical_owners.values_list(
                'id',
                flat=True,
            )),
            'environments': [e.child.id for e in environments]
        }
