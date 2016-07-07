import logging
from functools import wraps

import pyhermes
from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver
from pyhermes import publisher

from ralph.business.models import (
    RoleProperty,
    RolePropertyValue,
    Venture,
    VentureRole
)
from ralph.discovery.models import Device, DeviceType

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
                    result = func(sender, instance, **kwargs)
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


def get_device_data(device, fields=None):
    """
    Returns dictonary with device data.
    """
    asset = device.get_asset(manager='admin_objects')
    if not asset:
        return {}
    mgmt_ip = device.management_ip
    data = {
        'id': asset.id,
        'hostname': device.name,
        'management_ip': mgmt_ip.address if mgmt_ip else '',
        'management_hostname': mgmt_ip.hostname if mgmt_ip else '',
        'service': device.service.uid if device.service else None,
        'environment': device.device_environment_id,
        'venture_role': device.venture_role_id,
        'custom_fields': _get_custom_fields(device),
    }
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
    return {
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
