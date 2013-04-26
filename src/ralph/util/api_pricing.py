# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ralph.business.models import Venture
from ralph.discovery.models import Device, DeviceType


def get_ventures():
    """Yields dicts describing all the ventures to be imported into pricing."""

    for venture in Venture.objects.select_related('department').all():
        department = venture.get_department()
        yield {
            'id': venture.id,
            'parent_id': venture.parent_id,
            'name': venture.name,
            'department': department.name if department else '',
        }


def get_devices():
    """Yields dicts describing all the devices to be imported into pricing."""

    virtual = {
        DeviceType.virtual_server,
        DeviceType.cloud_server,
        DeviceType.mogilefs_storage,
    }
    for device in Device.objects.select_related('model').exclude(
        model__type__in=virtual,
        deleted=True,
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
        deleted=False,
    ):
        cores = device.get_core_count()
        if not cores:
            continue
        yield {
            'device_id': device.id,
            'venture_id': device.venture_id,
            'physical_cores': cores,
        }
