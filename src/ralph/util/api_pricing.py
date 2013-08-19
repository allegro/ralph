# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.business.models import Venture
from ralph.discovery.models import Device, DeviceType, DiskShareMount

from django.db import models as db


def get_ventures():
    """Yields dicts describing all the ventures to be imported into pricing."""

    for venture in Venture.objects.select_related('department').all():
        department = venture.get_department()
        yield {
            'id': venture.id,
            'parent_id': venture.parent_id,
            'name': venture.name,
            'department': department.name if department else '',
            'symbol': venture.symbol,
            'business_segment': venture.business_segment.name if
            venture.business_segment else "",
            'profit_center': venture.profit_center.name if
            venture.profit_center else "",
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


def get_virtual_usages():
    """Yields dicts reporting the number of virtual cores, memory and disk."""

    for device in Device.objects.filter(model__type=DeviceType.virtual_server):
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

def get_shares():
    """Yields dicts reporting the storage shares for all servers."""

    for mount in DiskShareMount.objects.select_related(
        'share',
    ).filter(is_virtual=False):
        yield {
            'storage_device_id': mount.share.device_id,
            'mount_device_id': mount.device_id,
            'model': (
                mount.share.model.group.name
                if mount.share.model.group
                else mount.share.model.name
            ),
            'label': mount.share.label,
            'size': mount.get_size(),
            'share_mount_count': mount.get_total_mounts(),
        }

