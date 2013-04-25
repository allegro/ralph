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

    for device in Device.objects.select_related('model').filter(deleted=False):
        yield {
            'id': device.id,
            'name': device.name,
            'parent_id': device.parent_id,
            'venture_id': device.venture_id,
            'is_virtual': device.model.type == DeviceType.virtual_server,
            'is_blade': device.model.type == DeviceType.blade_server,
        }


def get_device_components(sn):
    """Yields dicts describing all device components to be taken in assets"""
    try:
        ralph_device = Device.objects.get(sn=sn)
    except Device.DoesNotExist:
        yield {}
    else:
        components = ralph_device.get_components
        for processor in components.get('processors'):
            yield {
                'model_proposed': processor.model.name,
            }
        for memory in components.get('memory'):
            yield {
                'model_proposed': memory.model.name,
            }
        for storage in components.get('storages'):
            yield {
                'model_proposed': storage.model.name,
                'sn': storage.sn,
            }
        for ethernet in components.get('ethernets'):
            yield {
                'model_proposed': ethernet,
                'sn': ethernet.mac,
            }
        for fibrechannel in components.get('fibrechannels'):
            yield {
                'model_proposed': fibrechannel.model.name,
                'sn': fibrechannel.mac,
            }
