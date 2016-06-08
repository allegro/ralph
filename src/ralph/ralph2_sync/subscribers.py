# -*- coding: utf-8 -*-
import logging
import pyhermes

from django.contrib.contenttypes.models import ContentType

from ralph.assets.models import AssetModel
from ralph.data_center.models import DataCenterAsset
from ralph.data_importer.models import ImportedObjects

logger = logging.getLogger(__name__)

model_mapping = {
    'Asset': DataCenterAsset,
    'AssetModel': AssetModel,
}


@pyhermes.subscriber(topic='ralph2_sync_ack')
def ralph2_sync_ack(data):
    """
    Receives ACK from Ralph2 and checks if there is ImportedObject entry for
    synced objects. Creates new ImportedObject entry if not exists before.
    """
    model = model_mapping[data['model']]
    ct = ContentType.objects.get_for_model(model)
    try:
        ImportedObjects.objects.get(
            content_type=ct,
            object_pk=data['ralph3_id']
        )
        logger.info(
            'ImportedObject mapping for {} found in Ralph3'.format(data)
        )
    except ImportedObjects.DoesNotExist:
        logger.info(
            'Creating new ImportedObject mapping in Ralph3: {}'.format(data)
        )
        ImportedObjects.objects.create(
            content_type=ContentType.objects.get_for_model(model),
            old_object_pk=data['id'],
            object_pk=data['ralph3_id'],
        )
