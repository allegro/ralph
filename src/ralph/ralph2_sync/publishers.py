# -*- coding: utf-8 -*-
import logging
from functools import wraps

import pyhermes

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.assets.models import AssetModel
from ralph.data_center.models import DataCenterAsset
from ralph.data_importer.models import ImportedObjects

logger = logging.getLogger(__name__)


def ralph2_sync(model):
    """
    Decorator for synchronizers with Ralph2. Decorated function should return
    dict with event data. Decorated function name is used as a topic name and
    dispatch_uid for post_save signal.
    """
    def wrap(func):
        # publish only if sync enabled (globally and for particular
        # function)
        if (
            settings.RALPH2_HERMES_SYNC_ENABLED and
            func.__name__ in settings.RALPH2_HERMES_SYNC_FUNCTIONS
        ):
            @wraps(func)
            # connect to post_save signal for a model
            @receiver(
                post_save, sender=model, dispatch_uid=func.__name__,
            )
            # register publisher
            @pyhermes.publisher(topic=func.__name__)
            def wrapped_func(sender, instance=None, created=False, **kwargs):
                # process the signal only if instance has not attribute
                # `_handle_post_save` set to False
                if getattr(instance, '_handle_post_save', True):
                    try:
                        result = func(sender, instance, created, **kwargs)
                        pyhermes.publish(func.__name__, result)
                    except:
                        logger.exception('Error during Ralph2 sync')
                    else:
                        return result
        else:
            # by default this would be standalone function, not attached to any
            # signal
            wrapped_func = func
        return wrapped_func
    return wrap


def _get_obj_id_ralph_20(obj):
    """
    Returns ID of object in Ralph2 or None if not found.
    """
    if not obj:
        return None
    pk = None
    content_type = ContentType.objects.get_for_model(obj._meta.model)
    try:
        imported_obj = ImportedObjects.objects.get(
            object_pk=obj.pk,
            content_type=content_type,
        )
        pk = imported_obj.old_object_pk
    except (obj._meta.model.DoesNotExist, ImportedObjects.DoesNotExist):
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
        'ralph2_id': _get_obj_id_ralph_20(asset),

        'service': asset.service_env.service.uid,
        'environment': _get_obj_id_ralph_20(
            asset.service_env.environment
        ),

        'force_depreciation': asset.force_depreciation,

        # location
        'data_center': _get_obj_id_ralph_20(
            asset.rack.server_room.data_center
        ) if asset.rack else None,
        'server_room': (
            _get_obj_id_ralph_20(asset.rack.server_room)
            if asset.rack else None
        ),
        'rack': _get_obj_id_ralph_20(asset.rack),
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
        data[field] = _get_obj_id_ralph_20(getattr(asset, field, None))
    return data


@ralph2_sync(AssetModel)
def sync_model_to_ralph2(sender, instance=None, created=False, **kwargs):
    """
    Publish AssetModel info to sync it in Ralph3.
    """
    model = instance
    return {
        'id': model.id,
        'ralph2_id': _get_obj_id_ralph_20(model),
        'name': model.name,
        'category': _get_obj_id_ralph_20(model.category),
        'cores_count': model.cores_count,
        'power_consumption': model.power_consumption,
        'height_of_device': model.height_of_device,
        'manufacturer': _get_obj_id_ralph_20(model.manufacturer),
    }
