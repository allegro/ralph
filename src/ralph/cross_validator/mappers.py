from ralph.cross_validator.ralph2.device import Asset
from ralph.data_center.models import DataCenterAsset
"""
mappers = {
    Ralph3Model: {
        'ralph2_model': Ralph2Model,
        'fields': {
            'name': ('old_field', 'new_field')
        },
        'blacklist': ['id']
    }
}
"""
mappers = {
    DataCenterAsset: {
        'ralph2_model': Asset,
        'fields': {
            'sn': ('sn', 'sn'),
            'niw': ('niw', 'niw'),
            'barcode': ('barcode', 'barcode'),
            'hostname': ('device_info__ralph_device__name', 'hostname',),
            'position': ('device_info__position', 'position'),
            'slot_no': ('device_info__slot_no', 'slot_no'),
            'management_ip': ('device_info__slot_no', 'management_ip'),
        },
        'blacklist': ['id', 'parent_id']
    }
}
