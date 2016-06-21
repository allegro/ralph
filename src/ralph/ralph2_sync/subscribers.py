# -*- coding: utf-8 -*-
import logging
from functools import wraps

import pyhermes
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from ralph.assets.models import AssetModel, Environment, ServiceEnvironment
from ralph.data_center.models import DataCenterAsset
from ralph.data_importer.models import ImportedObjects

logger = logging.getLogger(__name__)

model_mapping = {
    'Asset': DataCenterAsset,
    'AssetModel': AssetModel,
}


class sync_subscriber(pyhermes.subscriber):
    """
    Log additional exception when sync has failed.
    """
    def _get_wrapper(self, func):
        @wraps(func)
        @transaction.atomic
        def exception_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logger.exception('Exception during syncing')
        return exception_wrapper


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


@sync_subscriber(topic='sync_device_to_ralph3')
def sync_device_to_ralph3(data):
    """
    Receive data about device from Ralph2

    Supported fields:
    * hostname
    * service/env
    * management ip/hostname
    """
    dca = ImportedObjects.get_object_from_old_pk(DataCenterAsset, data['id'])
    dca.hostname = data['hostname']
    dca.management_ip = data['management_ip']
    dca.management_hostname = data['management_hostname']
    if data['service'] and data['environment']:
        dca.service_env = ServiceEnvironment.objects.get(
            service__uid=data['service'],
            environment=ImportedObjects.get_object_from_old_pk(
                Environment, data['environment']
            )
        )
    # don't trigger another publishing event
    dca._handle_post_save = False
    dca.save()
