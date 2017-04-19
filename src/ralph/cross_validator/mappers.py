from ralph.admin.helpers import get_value_by_relation_path
from ralph.cross_validator.ralph2.device import (
    Asset,
    AssetModel as Ralph2AssetModel
)
from ralph.cross_validator.helpers import get_obj_id_ralph_20
from ralph.data_center.models import DataCenterAsset
from ralph.assets.models import AssetModel

"""
def return_diff(old, new):
    if old != new:
        return {
            'old': 'old value',
            'new': 'new_value'
        }

mappers = {
    Ralph3Model: {
        'ralph2_model': Ralph2Model,
        'fields': {
            'name': ('old_field', 'new_field')  # or something callable
            'model': return_diff
        },
        'blacklist': ['id']
    }
}
"""


def service_env_diff(old, new):
    old_uid = old.linked_device.service.uid if old.linked_device and old.linked_device.service else None  # noqa
    old_env = old.linked_device.device_environment.name if old.linked_device and old.linked_device.device_environment else None  # noqa
    new_uid = new.service_env.service.uid if new.service_env else None
    new_env = new.service_env.environment.name if new.service_env else None
    if old_uid != new_uid or old_env != new_env:
        return {
            'old': '{} | {}'.format(
                old.linked_device.service.name if old.linked_device else '',
                old_env
            ),
            'new': '{} | {}'.format(
                new.service_env.service.name if new.service_env else '',  # noqa
                new_env
            ),
        }


def device_model_diff(old, new):
    try:
        old_model_id = old.model.id
    except AttributeError:
        old_model_id = None
    new_model_id = get_obj_id_ralph_20(new.model)
    if old_model_id != str(new_model_id):
        return {
            'old': '{} | {}'.format(old.model.name, old_model_id),
            'new': '{} | {}'.format(new.model.name, new_model_id),
        }


def foreign_key_diff(old_path, new_path):
    def diff(old, new):
        old_fk_obj = get_value_by_relation_path(old, old_path)
        new_fk_obj_pk = get_obj_id_ralph_20(get_value_by_relation_path(new, new_path))  # noqa
        if getattr(old_fk_obj, 'pk', None) != new_fk_obj_pk:
            return {
                'old': '{}'.format(getattr(old_fk_obj, 'pk', None)),
                'new': '{}'.format(new_fk_obj_pk),
            }
    return diff


mappers = {
    DataCenterAsset: {
        'ralph2_model': Asset,
        'fields': {
            'sn': ('sn', 'sn'),
            'niw': ('niw', 'niw'),
            'barcode': ('barcode', 'barcode'),
            'hostname': ('device_info__ralph_device__name', 'hostname',),
            'slot_no': ('device_info__slot_no', 'slot_no'),
            'management_ip': ('device_info__slot_no', 'management_ip'),
            'model': device_model_diff,
            'service_env': service_env_diff,

            'position': ('device_info__position', 'position'),
            'rack': foreign_key_diff('device_info__rack', 'rack')
        },
        'blacklist': ['id', 'parent_id']
    },
    AssetModel: {
        'ralph2_model': Ralph2AssetModel,
        'fields': {
            'name': ('name', 'name')
        },
        'blacklist': ['id']
    }
}
