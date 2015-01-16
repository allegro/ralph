# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db

from ralph.cmdb.models import CI, CIAttributeValue, CIOwner, CIType
from ralph.discovery.models import (
    Database,
    Device,
    DeviceEnvironment,
    DeviceType,
    DiskShareMount,
    FibreChannel,
    IPAddress,
    LoadBalancerVirtualServer,
)
from ralph.util.api import Getter


def get_virtual_usages(parent_service_uid=None):
    """Yields dicts reporting the number of virtual cores, memory and disk."""
    devices = Device.objects.filter(
        model__type=DeviceType.virtual_server
    ).select_related('model')
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
            'model_id': device.model_id,
            'model_name': device.model.name,
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


class get_environments(Getter):
    Model = DeviceEnvironment
    fields = [
        ('ci_id', 'id'),
        ('ci_uid', 'uid'),
        'name'
    ]


def get_openstack_tenants(model_name=None):
    tenants = Device.objects.filter(
        sn__startswith='openstack',
        model__type=DeviceType.cloud_server
    )
    if model_name:
        tenants = tenants.filter(model__name=model_name)
    for tenant in tenants:
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


class get_vips(Getter):
    Model = LoadBalancerVirtualServer

    fields = [
        ('vip_id', 'id'),
        'name',
        ('ip_address', 'address__address'),
        ('type_id', 'load_balancer_type_id'),
        ('type', 'load_balancer_type__name'),
        'service_id',
        ('environment_id', 'device_environment_id'),
        'device_id',
        'port',
    ]

    def __init__(self, parent_service_uid=None, load_balancer_type=None):
        self.parent_service_uid = parent_service_uid
        self.load_balancer_type = load_balancer_type

    def get_queryset(self):
        result = super(get_vips, self).get_queryset()
        if self.parent_service_uid:
            result = result.filter(
                device__service__uid=self.parent_service_uid
            )
        if self.load_balancer_type:
            result = result.filter(
                load_balancer_type__name=self.load_balancer_type
            )
        return result


class get_databases(Getter):
    Model = Database

    fields = [
        ('database_id', 'id'),
        'name',
        ('type_id', 'database_type_id'),
        ('type', 'database_type__name'),
        'service_id',
        ('environment_id', 'device_environment_id'),
        'parent_device_id',
    ]

    def __init__(self, parent_service_uid=None, database_type=None):
        self.parent_service_uid = parent_service_uid
        self.database_type = database_type

    def get_queryset(self):
        result = super(get_databases, self).get_queryset()
        if self.parent_service_uid:
            result = result.filter(
                parent_device__service__uid=self.parent_service_uid
            )
        if self.database_type:
            result = result.filter(
                database_type__name=self.database_type
            )
        return result


# CMDB
class get_business_lines(Getter):
    """
    Returns Business Lines from CMDB (CIs with type Business Line)
    """
    Model = CI

    @property  # When testing the table won't exist during import
    def filters(self):
        return {'type': CIType.objects.get(name='BusinessLine')}

    fields = [
        ('ci_id', 'id'),
        ('ci_uid', 'uid'),
        'name',
    ]


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


class get_owners(Getter):
    """
    Returns CIOwners from CMDB
    """
    Model = CIOwner
    fields = ['id', 'profile_id']


def get_services(only_calculated_in_scrooge=False):
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
        try:
            calculate_in_scrooge = service.ciattributevalue_set.get(
                attribute_id=7
            ).value
        except CIAttributeValue.DoesNotExist:
            calculate_in_scrooge = False
        if only_calculated_in_scrooge and not calculate_in_scrooge:
            continue

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
