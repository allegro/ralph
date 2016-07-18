import ipaddr
import logging
import re
from functools import wraps

import pyhermes
from django.conf import settings

from django.core.exceptions import MultipleObjectsReturned
from django.db.models.signals import post_save
from django.dispatch import receiver
from pyhermes import publisher

from ralph.business.models import (
    RoleProperty,
    RolePropertyValue,
    Venture,
    VentureRole
)
from ralph.discovery.models import (
    Device, DeviceType, Network, NetworkKind, Environment
)
from ralph.dnsedit.models import DHCPEntry
from ralph.export_to_ng.resources import get_data_center_id
from ralph_assets.models_dc_assets import Rack

logger = logging.getLogger(__name__)


def ralph3_sync(model, topic=None):
    """
    Decorator for synchronizers with Ralph3. Decorated function should return
    dict with event data. Decorated function name is used as a topic name and
    dispatch_uid for post_save signal.
    """
    def wrap(func):
        topic_name = topic or func.__name__

        @wraps(func)
        # connect to post_save signal for a model
        @receiver(
            post_save, sender=model, dispatch_uid=func.__name__,
        )
        # register publisher
        @pyhermes.publisher(topic=topic_name)
        def wrapped_func(sender, instance=None, **kwargs):
            if (
                # publish only if sync enabled (globally and for particular
                # function)
                settings.RALPH3_HERMES_SYNC_ENABLED and
                topic_name in settings.RALPH3_HERMES_SYNC_FUNCTIONS and
                # process the signal only if instance has not attribute
                # `_handle_post_save` set to False
                getattr(instance, '_handle_post_save', True)
            ):
                try:
                    if result:
                        pyhermes.publish(topic_name, result)
                except Exception as e:
                    logger.exception(
                        'Error during Ralph2 sync ({})'.format(str(e))
                    )
                else:
                    return result

        # store additional info about signal
        wrapped_func._signal_model = model
        wrapped_func._signal_dispatch_uid = func.__name__
        wrapped_func._signal_type = post_save
        return wrapped_func
    return wrap


@publisher(topic='ralph2_sync_ack', auto_publish_result=True)
def publish_sync_ack_to_ralph3(obj, ralph3_id):
    """
    Publish ACK to Ralph3 that some object was updated.
    """
    return {
        'model': obj._meta.object_name,
        'id': obj.id,
        'ralph3_id': ralph3_id,
    }


def _get_custom_fields(device):
    result = {}
    if device.venture_role:
        for key, value in device.venture_role.get_properties(device).items():
            if key in settings.RALPH2_HERMES_ROLE_PROPERTY_WHITELIST:
                result[key] = value if value is not None else ''
    return result


def _get_ips_list(device):
    ips_list = []

    def get_mac(ip):
        mac = ''
        try:
            mac = DHCPEntry.objects.get(ip=ip.address).mac
        except DHCPEntry.DoesNotExist:
            pass
        except MultipleObjectsReturned:
            logger.exception('Multiple entries in DCHP for {}'.format(
                ip.address
            ))
        return mac

    for ip in device.ipaddress_set.all():
        mac = get_mac(ip)
        ips_list.append({
            'address': ip.address,
            'hostname': ip.hostname,
            'is_management': ip.is_management,
            'mac': mac,
            'dhcp_expose': bool(mac)
        })
    return {
        'ips': ips_list
    }


def get_device_data(device, fields=None):
    """
    Returns dictonary with device data.
    """
    asset = device.get_asset(manager='admin_objects')
    if not asset:
        return {}
    data = {
        'id': asset.id,
        'hostname': device.name,
        'service': device.service.uid if device.service else None,
        'environment': device.device_environment_id,
        'venture_role': device.venture_role_id,
        'custom_fields': _get_custom_fields(device),
    }
    data.update(_get_ips_list(device))
    return {k: v for k, v in data.items() if k in fields} if fields else data


@ralph3_sync(Device)
def sync_device_to_ralph3(sender, instance=None, **kwargs):
    """
    Send device data when device was saved.
    """
    return get_device_data(instance, fields=kwargs.get('_sync_fields'))


@ralph3_sync(RolePropertyValue, topic='sync_device_to_ralph3')
def sync_device_properties_to_ralph3(sender, instance=None, **kwargs):
    """
    Send device data when properties was changed.
    """
    device = instance.device
    return get_device_data(device, fields=['id', 'custom_fields'])


@ralph3_sync(Venture)
def sync_venture_to_ralph3(sender, instance=None, created=False, **kwargs):
    """
    Send venture info to Ralph3.

    Notice that in case of saving Venture, child sub-ventures are not synced
    (although they are saved in Venture.save).
    """
    venture = instance
    data = {
        'id': venture.id,
        'symbol': venture.symbol,
        'parent': venture.parent_id,
        'department': venture.department.name if venture.department else None,
    }
    return data


@ralph3_sync(VentureRole)
def sync_venture_role_to_ralph3(sender, instance=None, created=False, **kwargs):
    """
    Send venture role info to Ralph3.
    """
    venture_role = instance
    data = {
        'id': venture_role.id,
        # publish full name instead of single name (based on puppet classifier)
        'name': venture_role.full_name.replace(' / ', '__'),
        'venture': venture_role.venture_id,
    }
    return data


@ralph3_sync(RoleProperty)
def sync_role_property_to_ralph3(sender, instance=None, created=False, **kwargs):
    """
    Send role property info to Ralph3
    """
    role_property = instance
    if role_property.symbol not in settings.RALPH2_HERMES_ROLE_PROPERTY_WHITELIST:  # noqa
        return {}
    choices = []
    if role_property.type:
        choices = list(
            role_property.type.rolepropertytypevalue_set.all().values_list(
                'value', flat=True
            )
        )
    data = {
        'symbol': role_property.symbol,
        'default': role_property.default,
        'choices': choices
    }
    return data


@ralph3_sync(Device)
def sync_virtual_server_to_ralph3(sender, instance=None, created=False, **kwargs):
    if not instance.model or instance.model.type != DeviceType.virtual_server:
        return
    asset = instance.parent.get_asset(manager='admin_objects') if instance.parent else None  # noqa
    data = {
        'id': instance.id,
        'type': instance.model.name if instance.model else None,
        'hostname': instance.name,
        'sn': instance.sn,
        'service': instance.service.uid if instance.service else None,
        'environment': instance.device_environment_id,
        'venture_role': instance.venture_role_id,
        'parent_id': asset.id if asset else None,
        'custom_fields': _get_custom_fields(instance),
    }
    data.update(_get_ips_list(instance))
    return data


@ralph3_sync(Environment)
def sync_network_environment_to_ralph3(sender, instance=None, created=False, **kwargs):
    def convert_template(instance):
        """Handle template without pipe inside"""
        template = instance.hosts_naming_template
        counter_result = re.search('<([0-9]+),([0-9]+)>', template)
        if not counter_result:
            logger.info(
                'Incorrect template for network environment with id {}. Return default values.'.format(instance.id)  # noqa
            )
            return {
                'hostname_template_prefix': '',
                'hostname_template_counter_length': 4,
                'hostname_template_postfix': '.{}'.format(instance.domain)
            }
        start = template.find('<')
        end = template.rfind('>')
        counter_min, counter_max = counter_result.groups()

        prefix = template[:start] + counter_min[0]
        data = {
            'hostname_template_prefix': prefix,
            'hostname_template_counter_length': max(len(counter_min), len(counter_max)) - 1,  # noqa
            'hostname_template_postfix': template[end + 1:]
        }
        return data

    data = {
        'id': instance.id,
        'name': instance.name,
        'data_center_id': get_data_center_id(instance.data_center),
        'domain': instance.domain,
        'remarks': instance.remarks,
    }
    data.update(convert_template(instance))
    return data


@ralph3_sync(NetworkKind)
def sync_network_kind_to_ralph3(sender, instance=None, created=False, **kwargs):
    return {
        'id': instance.id,
        'name': instance.name
    }


@ralph3_sync(Network)
def sync_network_to_ralph3(sender, instance=None, created=False, **kwargs):
    net = instance

    def get_reserved_ips(net):
        start = net.min_ip
        end = net.max_ip
        bottom, top = net.reserved, net.reserved_top_margin
        # start + 1 , start is reserved for network address
        for int_ip in xrange(start + 1, start + bottom + 1):
            yield str(ipaddr.IPAddress(int_ip))
        # end - 1 , end is reserved for broadcast address
        for int_ip in xrange(end - 1, end - top - 1, -1):
            yield str(ipaddr.IPAddress(int_ip))

    def get_racks_ids(net):
        for rack in net.racks.all():
            try:
                yield Rack.objects.get(
                    deprecated_ralph_rack_id=rack.id
                ).id
            except Rack.DoesNotExist:
                pass

    try:
        network_address = ipaddr.IPNetwork(net.address, strict=True)
    except ValueError:
        network_address = ipaddr.IPNetwork(net.address)
        logger.info('Network {} will be converted to {}/{}'.format(
            network_address,
            network_address.network,
            network_address.prefixlen
        ))

    return {
        'id': net.id,
        'name': net.name,
        'address': '{}/{}'.format(
            network_address.network, network_address.prefixlen
        ),
        'remarks': net.remarks,
        'vlan': net.vlan,
        'dhcp_broadcast': net.dhcp_broadcast,
        'gateway': net.gateway,
        'reserved_ips': list(get_reserved_ips(net)) if net.min_ip and net.max_ip else [],  # noqa
        'environment_id': net.environment_id,
        'kind_id': net.kind_id,
        'racks_ids': list(get_racks_ids(net)) if net.racks.count() else [],
        'dns_servers': list(
            net.custom_dns_servers.all().values_list('ip_address', flat=True)  # noqa
        ),
    }


@ralph3_sync(Device)
def sync_stacked_switch_to_ralph3(sender, instance=None, created=False, **kwargs):
    if not instance.model or instance.model.type != DeviceType.switch_stack:
        return

    child_devices = []
    for child in instance.logicalchild_set.all().order_by('-name'):
        asset = child.get_asset(manager='admin_objects')
        if asset:
            child_devices.append(
                # mark is_master as True when it's first child
                {'asset_id': asset.id, 'is_master': bool(child_devices)}
            )
        else:
            logger.error('Asset not found for child device {}'.format(child))

    data = {
        'id': instance.id,
        'type': instance.model.name if instance.model else None,
        'hostname': instance.name,
        'service': instance.service.uid if instance.service else None,
        'environment': instance.device_environment_id,
        'venture_role': instance.venture_role_id,
        'custom_fields': _get_custom_fields(instance),
        'child_devices': child_devices,
    }
    data.update(_get_ips_list(instance))
    return data
