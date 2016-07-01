# -*- coding: utf-8 -*-
import logging
from functools import wraps

import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.assets.models import (
    AssetModel,
    ConfigurationClass,
    ConfigurationModule
)
from ralph.data_center.models import DataCenterAsset, Rack
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)

logger = logging.getLogger(__name__)

print('load publishers')

def ralph2_sync(model):
    """
    Decorator for synchronizers with Ralph2. Decorated function should return
    dict with event data. Decorated function name is used as a topic name and
    dispatch_uid for post_save signal.
    """
    def wrap(func):
        @wraps(func)
        # connect to post_save signal for a model
        @receiver(
            post_save, sender=model, dispatch_uid=func.__name__,
        )
        # register publisher
        @pyhermes.publisher(topic=func.__name__)
        def wrapped_func(sender, instance=None, created=False, **kwargs):
            # publish only if sync enabled (globally and for particular
            # function)
            if (
                settings.RALPH2_HERMES_SYNC_ENABLED and
                func.__name__ in settings.RALPH2_HERMES_SYNC_FUNCTIONS and
                # process the signal only if instance has not attribute
                # `_handle_post_save` set to False
                getattr(instance, '_handle_post_save', True)
            ):
                try:
                    result = func(sender, instance, created, **kwargs)
                    pyhermes.publish(func.__name__, result)
                except:
                    logger.exception('Error during Ralph2 sync')
                else:
                    return result
        # store additional info about signal
        wrapped_func._signal_model = model
        wrapped_func._signal_dispatch_uid = func.__name__
        wrapped_func._signal_type = post_save
        return wrapped_func
    return wrap


def _get_obj_id_ralph_2(obj):
    """
    Returns ID of object in Ralph2 or None if not found.
    """
    if not obj:
        return None
    pk = None
    try:
        pk = ImportedObjects.get_imported_id(obj)
    except ImportedObjectDoesNotExist:
        pass
    return pk


@ralph2_sync(DataCenterAsset)
def sync_dc_asset_to_ralph2(sender, instance=None, created=False, **kwargs):
    """
    Publish information about DataCenterAsset after change to sync it in Ralph2.

    Known situations when this sync will not work:
    * new rack/server room/data center added (it's not synced with Ralph2)
    """
    asset = instance
    data = {
        'ralph2_id': _get_obj_id_ralph_2(asset),

        'service': asset.service_env.service.uid,
        'environment': _get_obj_id_ralph_2(
            asset.service_env.environment
        ),

        'force_depreciation': asset.force_depreciation,

        # location
        'data_center': _get_obj_id_ralph_2(
            asset.rack.server_room.data_center
        ) if asset.rack else None,
        'server_room': (
            _get_obj_id_ralph_2(asset.rack.server_room)
            if asset.rack else None
        ),
        'rack': _get_obj_id_ralph_2(asset.rack),
    }
    # simple fields
    for field in [
        'id', 'orientation', 'position', 'sn', 'barcode', 'slot_no',
        'price', 'niw', 'task_url', 'remarks', 'order_no', 'invoice_date',
        'invoice_no', 'provider', 'source', 'status', 'depreciation_rate',
        'depreciation_end_date', 'management_ip', 'management_hostname',
        'hostname'
    ]:
        data[field] = str(getattr(asset, field, '') or '')
    # foreign key fields
    for field in [
        'model', 'property_of',
    ]:
        data[field] = _get_obj_id_ralph_2(getattr(asset, field, None))
    return data


@ralph2_sync(AssetModel)
def sync_model_to_ralph2(sender, instance=None, created=False, **kwargs):
    """
    Publish AssetModel info to sync it in Ralph3.
    """
    model = instance
    return {
        'id': model.id,
        'ralph2_id': _get_obj_id_ralph_2(model),
        'name': model.name,
        'category': _get_obj_id_ralph_2(model.category),
        'cores_count': model.cores_count,
        'power_consumption': model.power_consumption,
        'height_of_device': model.height_of_device,
        'manufacturer': _get_obj_id_ralph_2(model.manufacturer),
    }


@ralph2_sync(Rack)
def sync_rack_to_ralph2(sender, instance=None, created=False, **kwargs):
    """
    Publish Rack info to sync it in Ralph3.
    """
    rack = instance
    return {
        'id': rack.id,
        'ralph2_id': _get_obj_id_ralph_2(rack),
        'name': rack.name,
        'description': rack.description,
        'orientation': rack.orientation,
        'max_u_height': rack.max_u_height,
        'visualization_col': rack.visualization_col,
        'visualization_row': rack.visualization_row,
        'server_room': _get_obj_id_ralph_2(rack.server_room),
        'data_center': _get_obj_id_ralph_2(rack.server_room.data_center) if rack.server_room else None,  # noqa


@ralph2_sync(ConfigurationModule)
def sync_configuration_module_to_ralph2(sender, instance=None, created=False, **kwargs):  # noqa
    """
    ConfigurationModule -> Venture
    """
    return {
        'id': instance.id,
        'ralph2_id': _get_obj_id_ralph_2(instance),
        'ralph2_parent_id': _get_obj_id_ralph_2(instance.parent) if instance.parent else None,  # noqa
        'symbol': instance.name,
        'department': instance.support_team.name if instance.support_team else None,  # noqa
    }


@ralph2_sync(ConfigurationClass)
def sync_configuration_class_to_ralph2(sender, instance=None, created=False, **kwargs):  # noqa
    """
    ConfigurationClass -> VentureRole
    """
    return {
        'id': instance.id,
        'ralph2_id': _get_obj_id_ralph_2(instance),
        'ralph2_parent_id': _get_obj_id_ralph_2(instance.module) if instance.module else None,  # noqa
        'symbol': instance.class_name,
    }
