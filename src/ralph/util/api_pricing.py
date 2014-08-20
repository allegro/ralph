# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import re

from django.db import models as db

from ralph.business.models import Venture, VentureExtraCost
from ralph.discovery.models import (
    Device,
    DeviceType,
    DiskShareMount,
    FibreChannel,
    HistoryCost,
    IPAddress,
)


DEVICE_REPR_RE = re.compile(r'^(?P<name>.*)[(](?P<id>\d+)[)]$')


def get_ventures():
    """Yields dicts describing all the ventures to be imported into pricing."""

    for venture in Venture.objects.select_related('department').all():
        department = venture.get_department()
        profit_center = None
        if venture.profit_center:
            profit_center = "{0} - {1}".format(
                venture.profit_center.name,
                venture.profit_center.description,
            )
        yield {
            'id': venture.id,
            'parent_id': venture.parent_id,
            'name': venture.name,
            'department': department.name if department else '',
            'symbol': venture.symbol,
            'business_segment': venture.business_segment.name if
            venture.business_segment else "",
            'profit_center': profit_center,
            'show_in_ralph': venture.show_in_ralph,
        }


def get_devices():
    """Yields dicts describing all the devices to be imported into pricing."""

    exclude = {
        DeviceType.cloud_server,
        DeviceType.mogilefs_storage,
    }
    for device in Device.objects.select_related('model').exclude(
        model__type__in=exclude,
    ):
        if device.model is None:
            continue
        yield {
            'id': device.id,
            'name': device.name,
            'sn': device.sn,
            'barcode': device.barcode,
            'parent_id': device.parent_id,
            'venture_id': device.venture_id,
            'is_virtual': device.model.type == DeviceType.virtual_server,
            'is_blade': device.model.type == DeviceType.blade_server,
        }


def get_physical_cores():
    """Yields dicts reporting the number of physical CPU cores on devices."""
    physical_servers = {
        DeviceType.blade_server,
        DeviceType.rack_server,
    }
    for device in Device.objects.filter(
        model__type__in=physical_servers,
    ):
        cores = device.get_core_count()
        if not cores:
            for system in device.operatingsystem_set.all():
                cores = system.cores_count
                if cores:
                    break
            else:
                continue
        yield {
            'device_id': device.id,
            'venture_id': device.venture_id,
            'physical_cores': cores,
        }


def get_virtual_usages(parent_venture_name=None):
    """Yields dicts reporting the number of virtual cores, memory and disk."""
    devices = Device.objects.filter(model__type=DeviceType.virtual_server)
    if parent_venture_name:
        devices = devices.filter(
            parent__venture=Venture.objects.get(
                name=parent_venture_name,
            ),
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
            'device_id': device.id,
            'venture_id': device.venture_id,
            'virtual_cores': cores or 0,
            'virtual_memory': memory or 0,
            'virtual_disk': disk or 0,
        }


def get_shares(venture_symbol=None, include_virtual=True):
    """
    Yields dicts reporting the storage shares mounts.

    :param venture_symbol: if passed, only share mounts from shares with
        storage device in this venture will be returned
    :param include_virtual: if False, virtual share mounts will be excluded
        from result
    """
    shares_mounts = DiskShareMount.objects.select_related(
        'share',
    )
    if not include_virtual:
        shares_mounts = shares_mounts.filter(is_virtual=False)
    if venture_symbol:
        shares_mounts = shares_mounts.filter(
            share__device__venture=Venture.objects.get(
                symbol=venture_symbol,
            )
        )
    for mount in shares_mounts:
        yield {
            'storage_device_id': mount.share.device_id,
            'mount_device_id': mount.device_id,
            'label': mount.share.label,
            'size': mount.get_size(),
        }


def get_extra_cost():
    for extracost in VentureExtraCost.objects.all():
        yield {
            'venture_id': extracost.venture_id,
            'venture': extracost.venture.name,
            'type': extracost.type.name,
            'cost': extracost.cost,
            'start': extracost.created,
            'end': extracost.expire,
        }


def devices_history(start_date, end_date):
    exclude = {
        DeviceType.cloud_server,
        DeviceType.mogilefs_storage,
    }
    for device in Device.admin_objects.exclude(
        model__type__in=exclude,
    ):
        date = start_date
        cores = device.get_core_count()
        data = {
            'device_id': device.id,
            'id': device.id,
            'date': date,
            'name': device.name,
            'sn': device.sn,
            'barcode': device.barcode,
            'parent_id': device.parent_id,
            'venture_id': device.venture_id,
            'is_virtual': device.model.type == DeviceType.virtual_server,
            'is_blade': device.model.type == DeviceType.blade_server,
            'virtual_cores': cores,
            'physical_cores': cores,
            'virtual_memory': sum(m.get_size() for m in device.memory_set.all()),
        }
        while date > end_date:
            date -= datetime.timedelta(days=1)
            if date < device.created.date():
                break
            day_changes = device.historychange_set.filter(date=date)
            day_costs = device.historycost_set.filter(end=date)
            data['date'] = date

            # Parent changes
            for change in day_changes.filter(
                field_name='.parent',
                component_id=None,
            ):
                if change.old_value == 'None':
                    data['parent_id'] = None
                else:
                    match = DEVICE_REPR_RE.match(change.new_value)
                    if match:
                        data['parent_id'] = int(match.group('id'))

            # Memory for virtual servers
            if data['is_virtual']:
                # we assume that if memory changes, it changes all at once
                memory_size = sum(
                    int(change.old_value)
                    for change in day_changes.filter(
                        field_name__endswith=').size',
                    ).exclude(component_id=None)
                    if 'Virtual RAM' in change.field_name
                )
                if memory_size:
                    data['virtual_memory'] = memory_size

            # Venture and CPU cores
            for cost in day_costs:
                data['venture_id'] = cost.venture_id
                data['virtual_cores'] = cost.cores
                data['physical_cores'] = cost.cores

            yield data


def get_device_by_name(device_name):
    """Returns device information by device name"""
    devices = Device.objects.filter(name=device_name)
    if devices:
        device = devices[0]
        return {
            'device_id': device.id,
            'venture_id': device.venture.id if device.venture else None,
        }
    return {}


def get_device_by_remarks(remark):
    """Returns device information by remark"""
    devices = Device.objects.filter(remarks__icontains=remark)
    if devices:
        device = devices[0]
        return {
            'device_id': device.id,
            'venture_id': device.venture.id if device.venture else None,
        }
    return {}


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


def get_cloud_daily_costs(date=None):
    """
    Returns cloud daily costs, grouped by venture.
    """
    if date is None:
        date = datetime.date.today()
    daily_costs = HistoryCost.objects.filter(
        device__model__type=DeviceType.cloud_server.id,
        end=date,
    ).values('venture__id').annotate(value=db.Sum('daily_cost'))
    for daily_cost in daily_costs:
        yield {
            'venture_id': daily_cost['venture__id'],
            'daily_cost': daily_cost['value']
        }


def get_fc_cards():
    for fc in FibreChannel.objects.values('id', 'device__id'):
        yield {
            'id': fc['id'],
            'device_id': fc['device__id'],
        }
