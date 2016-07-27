from django.conf import settings
from django.db.models import Prefetch

from ralph.admin.helpers import getattr_dunder
from ralph.assets.models import AssetModel, Ethernet
from ralph.cross_validator.additional_checkers import ralph2_dhcp_checker
from ralph.cross_validator.helpers import get_obj_id_ralph_20
from ralph.cross_validator.ralph2.device import AssetModel as Ralph2AssetModel
from ralph.cross_validator.ralph2.device import Asset, Device
from ralph.cross_validator.ralph2.network import DHCPEntry as Ralph2DHCPEntry
from ralph.cross_validator.ralph2.network import Network as Ralph2Network
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.dhcp.models import DHCPEntry
from ralph.networks.models import Network
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
    if dev and dev.venture_role:
        old_custom_fields = dev.venture_role.get_properties(dev)
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


def network_terminators_diff(old, new):
    old_terminators_names = set(old.terminators.values_list('name', flat=True))
    new_terminators_names = set(new.terminators.values_list(
        'asset__datacenterasset__hostname', flat=True
    ))
    diff = old_terminators_names - new_terminators_names
    if diff:
        return {
            'old': list(old_terminators_names),
            'new': list(new_terminators_names)
        }


def network_racks_diff(old, new):
    old_racks = set(old.racks.values_list('name', flat=True))
    new_racks = set(new.racks.values_list('name', flat=True))
    diff = old_racks - new_racks
    if diff:
        return {
            'old': list(old_racks),
            'new': list(new_racks)
        }


def network_dns_servers_diff(old, new):
    old_dns = set(old.custom_dns_servers.values_list('ip_address', flat=True))
    new_dns = set(new.dns_servers.values_list('ip_address', flat=True))
    diff = old_dns - new_dns
    if diff:
        return {
            'old': list(map(str, old_dns)),
            'new': list(map(str, new_dns))
        }


def network_reserved_bottom_diff(old, new):
    old_reserved = old.reserved
    new_reserved = new.reserved_bottom
    if old_reserved != new_reserved:
        return {
            'old': old_reserved,
            'new': new_reserved,
        }


def network_reserved_top_diff(old, new):
    old_reserved = old.reserved_top_margin
    new_reserved = new.reserved_top
    if old_reserved != new_reserved:
        return {
            'old': old_reserved,
            'new': new_reserved,
        }


def ip_diff(old_path, new_path):
    def diff(old, new):
        old_ip = str(getattr_dunder(old, old_path))
        new_ip = str(getattr_dunder(new, new_path))
        if old_ip != new_ip:
            return {
                'old': old_ip,
                'new': new_ip,
            }
    return diff


def compare_mac(old, new):
    def parse_mac(mac):
        return mac.lower().replace('-', '').replace(':', '')
    old_mac = parse_mac(old.mac)
    new_mac = parse_mac(new.mac)
    if new_mac != old_mac:
        return {
            'old': old.mac,
            'new': new.mac,
        }


def ips_diff(old, new):
    if isinstance(old, Asset):
        dev = old.linked_device
    else:
        dev = old
    if dev:
        old_ips = set([
            (str(ip.address), ip.hostname) for ip in dev.ipaddress_set.all()
        ])
    else:
        old_ips = set()
    new_ips = set([
        (str(ip.address), ip.hostname) for ip in new.ipaddresses.all()
    ])
    if old_ips != new_ips:
        return {
            'old': list(sorted(old_ips)),
            'new': list(sorted(new_ips)),
        }


def dhcp_entries_diff(old, new):
    if isinstance(old, Asset):
        dev = old.linked_device
    else:
        dev = old
    if dev:
        old_macs = set(eth.mac for eth in dev.ethernet_set.all())
        old_entries = set([(str(dhcp.ip), dhcp.mac) for dhcp in Ralph2DHCPEntry.objects.filter(mac__in=old_macs)])  # noqa
    else:
        old_entries = set()
    new_entries = set([(str(dhcp.address), dhcp.mac.replace(':', '')) for dhcp in DHCPEntry.objects.filter(ethernet__base_object=new)])  # noqa
    if old_entries != new_entries:
        return {
            'old': list(sorted(old_entries)),
            'new': list(sorted(new_entries)),
        }

mappers = {
    'DataCenterAsset': {
        'ralph2_model': Asset,
        'ralph3_model': DataCenterAsset,
        'ralph3_queryset': DataCenterAsset.objects.exclude(
            status=DataCenterAssetStatus.liquidated
        ).select_related(
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
            'device_info__ralph_device__ipaddress_set',
            'device_info__ralph_device__ethernet_set',
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
            'ips': ips_diff,
            'dhcp': dhcp_entries_diff,
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
            'ips': ips_diff,
            'dhcp': dhcp_entries_diff,
        },
        'blacklist': ['id'],
    },
    'DHCPEntry': {
        'ralph2_model': Ralph2DHCPEntry,
        'ralph3_model': DHCPEntry,
        # 'ralph2_queryset': Ralph2DHCPEntry.objects.exclude()
        'use_imported_object': False,
        'query_params': lambda new: {
            'ip': new.address,
            'mac': new.mac.replace(':', ''),
        },
        'fields': {
            'mac': compare_mac,
            'ip': ('ip', 'address')
        },
        'blacklist': ['id'],
        'additional_checkers': [ralph2_dhcp_checker]
    },
    'Network': {
        'ralph2_model': Ralph2Network,
        'ralph3_model': Network,
        'ralph3_queryset': Network.objects.all(),  # TODO: related
        'ralph2_queryset': Ralph2Network.objects.all(),
        'fields': {
            'address': ip_diff('address', 'address'),
            'gateway': ip_diff('gateway', 'gateway__address'),
            'remarks': ('remarks', 'remarks'),
            'terminators': network_terminators_diff,
            'vlan': ('vlan', 'vlan'),
            'racks': network_racks_diff,
            'network_environment': foreign_key_diff(
                'environment', 'network_environment'
            ),
            'kind': foreign_key_diff('kind', 'kind'),
            'dhcp_broadcast': ('dhcp_broadcast', 'dhcp_broadcast'),
            'dns_servers': network_dns_servers_diff,
            'reserved_bottom': network_reserved_bottom_diff,
            'reserved_top': network_reserved_top_diff,
        },
        'blacklist': ['id'],
    },
}
