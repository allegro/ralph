# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.business.models import Venture
from ralph.discovery.models import Device, DeviceType

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
            continue
        yield {
            'device_id': device.id,
            'venture_id': device.venture_id,
            'physical_cores': cores,
        }

def get_virtual_usages():
    """Yields dicts reporting the number of virtual cores, memory and disk."""

    for device in Device.objects.select_related('model').filter(
        model__type=DeviceType.virtual_server,
    ):
        cores = device.get_core_count()
        memory = device.memory_set.aggregate(db.Sum('size'))['size_sum']
        disk = device.storage_set.aggregate(db.Sum('size'))['size_sum']
        yield {
            'id': device.id,
            'venture_id': device.venture_id,
            'virtual_cores': cores,
            'virtual_memory': memory,
            'virtual_disk': disk,
        }

