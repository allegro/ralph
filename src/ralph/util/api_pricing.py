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

    for device in Device.objects.select_related(
            'model__type',
        ).filter(deleted=False):
        yield {
            'id': device.id,
            'name': device.name,
            'venture_id': device.venture_id,
            'is_virtual': device.model.type == DeviceType.virtual_server,
            'is_blade': device.model.type == DeviceType.blade_server,
        }
