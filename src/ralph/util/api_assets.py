# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ralph.discovery.models import Device


def get_devices():
    """Yields dicts describing all devices to be taken in assets"""
    for device in Device.admin_objects.all():
        yield {
            'device_id': device.id,
            'name': device.name,
            'sn': device.sn,
            'price': device.cached_price,
            'support_kind': device.support_kind,
            'remarks': device.remarks,
            'barcode': device.barcode,
            'purchase_date': device.purchase_date,
            'deleted': device.deleted,
        }


def get_device_components(sn):
    """Yields dicts describing all device components to be taken in assets"""
    try:
        ralph_device = Device.objects.get(sn=sn)
    except Device.DoesNotExist:
        raise LookupError('Device not found')
    else:
        components = ralph_device.get_components()
        for processor in components.get('processors', []):
            yield {
                'model_proposed': processor.model.name,
            }
        for memory in components.get('memory', []):
            yield {
                'model_proposed': memory.model.name,
            }
        for storage in components.get('storages', []):
            yield {
                'model_proposed': storage.model.name,
                'sn': storage.sn,
            }
        for ethernet in components.get('ethernets', []):
            yield {
                'model_proposed': unicode(ethernet),
                'sn': ethernet.mac,
            }
        for fibrechannel in components.get('fibrechannels', []):
            yield {
                'model_proposed': fibrechannel.model.name,
                'sn': fibrechannel.mac,
            }
