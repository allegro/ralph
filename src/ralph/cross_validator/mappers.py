from django.conf import settings
from django.db.models import Prefetch

from ralph.admin.helpers import getattr_dunder
from ralph.assets.models import AssetModel, Ethernet
from ralph.cross_validator.helpers import get_obj_id_ralph_20
from ralph.cross_validator.ralph2.device import AssetModel as Ralph2AssetModel
from ralph.cross_validator.ralph2.device import Asset, Device
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.virtual.models import VirtualServer

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
    old_uid = getattr_dunder(old, 'service__uid')
    old_env = getattr_dunder(old, 'device_environment__name')
    new_uid = getattr_dunder(new, 'service_env__service__uid')
    new_env = getattr_dunder(new, 'service_env__environment__name')
    if old_uid != new_uid or old_env != new_env:
        return {
            'old': '{} | {}'.format(
                getattr_dunder(old, 'linked_device__service__name', ''), old_env
            ),
            'new': '{} | {}'.format(
                getattr_dunder(new, 'service_env__service__name', ''), new_env
            ),
        }


def foreign_key_diff(old_path, new_path):
    def diff(old, new):
        old_fk_obj = getattr_dunder(old, old_path)
        new_fk_obj_pk = get_obj_id_ralph_20(getattr_dunder(new, new_path))
        if getattr(old_fk_obj, 'pk', None) != new_fk_obj_pk:
            return {
                'old': '{}'.format(getattr(old_fk_obj, 'pk', None)),
                'new': '{}'.format(new_fk_obj_pk),
            }
    return diff


def custom_fields_diff(old, new):
    if isinstance(old, Asset):
        dev = old.linked_device
    else:
        dev = old
    if dev:
        # TODO: respect whitelist of custom fields to sync
        old_custom_fields = dev.get_property_set()
    else:
        old_custom_fields = {}
    new_custom_fields = new.custom_fields_as_dict

    # filter to compare only imported Custom Fields
    def filter_cf(cf):
        return {
            k: v for (k, v) in cf.items()
            if k in settings.RALPH2_HERMES_ROLE_PROPERTY_WHITELIST
        }

    old_custom_fields = filter_cf(old_custom_fields)
    new_custom_fields = filter_cf(new_custom_fields)

    if old_custom_fields != new_custom_fields:
        return {
            'old': old_custom_fields,
            'new': new_custom_fields,
        }


def check_asset_has_device(old, new):
    if not old:
        return
    dev = old.linked_device
    if not dev and new.status != DataCenterAssetStatus.liquidated:
        return 'Asset has no linked device'


mappers = {
    'DataCenterAsset': {
        'ralph2_model': Asset,
        'ralph3_model': DataCenterAsset,
        'ralph3_queryset': DataCenterAsset.objects.select_related(
            'service_env__service', 'service_env__environment',
            'rack', 'model'
        ).prefetch_related(
            Prefetch(
                'ethernet_set',
                queryset=Ethernet.objects.select_related('ipaddress')
            ),
        ),
        'ralph2_queryset': Asset.objects.select_related(
            'device_info', 'device_info__rack', 'device_info__ralph_device',
            'model', 'device_info__ralph_device__parent',
            'device_info__ralph_device__logical_parent'
        ).prefetch_related(
            'device_info__ralph_device__ipaddress_set'
        ),
        'fields': {
            'sn': ('sn', 'sn'),
            'niw': ('niw', 'niw'),
            'barcode': ('barcode', 'barcode'),
            'hostname': ('device_info__ralph_device__name', 'hostname',),
            'slot_no': ('device_info__slot_no', 'slot_no'),
            'management_ip': (
                'device_info__ralph_device__management_ip', 'management_ip'
            ),
            'model': foreign_key_diff('model', 'model'),
            'service_env': service_env_diff,
            'position': ('device_info__position', 'position'),
            'rack': foreign_key_diff('device_info__rack', 'rack'),
            'venture': foreign_key_diff(
                'device_info__ralph_device__venture_role',
                'configuration_path'
            ),
            'custom_fields': custom_fields_diff,
        },
        'blacklist': ['id', 'parent_id'],
        'errors_checkers': [
            check_asset_has_device,
        ]
    },
    'AssetModel': {
        'ralph2_model': Ralph2AssetModel,
        'ralph3_model': AssetModel,
        'fields': {
            'name': ('name', 'name')
        },
        'blacklist': ['id']
    },
    'VirtualServer': {
        'ralph2_model': Device,
        'ralph3_model': VirtualServer,
        'ralph3_queryset': VirtualServer.objects.select_related(
            'service_env__service', 'service_env__environment',
            'type'
        ),
        'ralph2_queryset': Device.objects.select_related(
            'parent',
        ),
        'fields': {
            'sn': ('sn', 'sn'),
            'hostname': ('name', 'hostname'),
            'service_env': service_env_diff,
            'parent': foreign_key_diff(
                'parent__asset', 'parent__asset__datacenterasset'
            ),
            'venture': foreign_key_diff('venture_role', 'configuration_path'),
            'custom_fields': custom_fields_diff,
        },
        'blacklist': ['id'],
    },
}
