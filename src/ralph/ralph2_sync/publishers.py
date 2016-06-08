# -*- coding: utf-8 -*-
import pyhermes

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from ralph.assets.models import AssetModel
from ralph.data_center.models import DataCenterAsset
from ralph.data_importer.models import ImportedObjects


def _get_obj_id_ralph_20(obj):
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


@receiver(post_save, sender=DataCenterAsset)
@pyhermes.publisher(topic='sync_dc_asset_to_ralph2', auto_publish_result=True)
def sync_dc_asset_to_ralph2(sender, instance=None, created=False, **kwargs):
    asset = instance
    data = {
        'ralph2_id': _get_obj_id_ralph_20(asset),

        'service': _get_obj_id_ralph_20(asset.service_env.service),
        'environment': _get_obj_id_ralph_20(
            asset.service_env.environment
        ),

        'force_depreciation': asset.force_depreciation,

        # location
        'data_center': _get_obj_id_ralph_20(
            asset.rack.server_room.data_center
        ),
        'server_room': _get_obj_id_ralph_20(asset.rack.server_room),
        'rack': _get_obj_id_ralph_20(asset.rack),
    }
    # simple fields
    for field in [
        'id', 'orientation', 'position', 'sn', 'barcode', 'slot_no',
        'price', 'niw', 'task_url', 'remarks', 'order_no', 'invoice_date',
        'invoice_no', 'provider', 'source', 'status', 'depreciation_rate',
        'depreciation_end_date', 'management_ip', 'management_hostname'
    ]:
        data[field] = str(getattr(asset, field, '') or '')
    # foreign key fields
    for field in [
        'model', 'property_of',
    ]:
        data[field] = _get_obj_id_ralph_20(getattr(asset, field, None))
    return data


@receiver(post_save, sender=AssetModel)
@pyhermes.publisher(topic='sync_model_to_ralph2', auto_publish_result=True)
def sync_model_to_ralph2(sender, instance=None, created=False, **kwargs):
    model = instance
    return {
        'id': model.id,
        'category': _get_obj_id_ralph_20(model.category),
        'cores_count': model.cores_count,
        'power_consumption': model.power_consumption,
        'height_of_device': model.height_of_device,
        'manufacturer': _get_obj_id_ralph_20(model.manufacturer),
    }
