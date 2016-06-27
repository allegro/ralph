# -*- coding: utf-8 -*-
import logging
from contextlib import ExitStack
from functools import wraps

import pyhermes
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from ralph.accounts.models import Team
from ralph.assets.models import (
    AssetModel,
    ConfigurationClass,
    ConfigurationModule,
    Environment,
    ServiceEnvironment
)
from ralph.data_center.models import DataCenterAsset
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.ralph2_sync.helpers import WithSignalDisabled
from ralph.ralph2_sync.publishers import sync_dc_asset_to_ralph2

logger = logging.getLogger(__name__)

model_mapping = {
    'Asset': DataCenterAsset,
    'AssetModel': AssetModel,
}


def _get_publisher_signal_info(func):
    """
    Return signal info for publisher in format accepted by `WithSignalDisabled`.
    """
    return {
        'dispatch_uid': func._signal_dispatch_uid,
        'sender': func._signal_model,
        'signal': func._signal_type,
        'receiver': func,
    }


class sync_subscriber(pyhermes.subscriber):
    """
    Log additional exception when sync has failed.
    """
    def __init__(self, topic, disable_publishers=None):
        self.disable_publishers = disable_publishers or []
        super().__init__(topic)

    def _get_wrapper(self, func):
        @wraps(func)
        @transaction.atomic
        def exception_wrapper(*args, **kwargs):
            # disable selected publisher signals during handling subcriber
            with ExitStack() as stack:
                for publisher in self.disable_publishers:
                    stack.enter_context(WithSignalDisabled(
                        **_get_publisher_signal_info(publisher)
                    ))
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


@sync_subscriber(
    topic='sync_device_to_ralph3',
    disable_publishers=[sync_dc_asset_to_ralph2],
)
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
    if data['management_ip']:
        dca.management_ip = data['management_ip']
        dca.management_hostname = data['management_hostname']
    else:
        del dca.management_ip
    if data['service'] and data['environment']:
        dca.service_env = ServiceEnvironment.objects.get(
            service__uid=data['service'],
            environment=ImportedObjects.get_object_from_old_pk(
                Environment, data['environment']
            )
        )
    # TODO: handle venture_role field
    dca.save()


@sync_subscriber(topic='sync_venture_to_ralph3')
def sync_venture_to_ralph3(data):
    """
    Receive data about venture from Ralph2 (ConfigurationModule in Ralph3).

    Supported fields:
    * symbol
    * parent
    * team
    """
    creating = False
    try:
        conf_module = ImportedObjects.get_object_from_old_pk(
            ConfigurationModule, data['id']
        )
    except ImportedObjectDoesNotExist:
        creating = True
        conf_module = ConfigurationModule()
        logger.info(
            'Configuration module {} ({}) not found - creating new one'.format(
                data['symbol'], data['id']
            )
        )

    if data['parent']:
        try:
            conf_module.parent = ImportedObjects.get_object_from_old_pk(
                ConfigurationModule, data['parent']
            )
        except ImportedObjectDoesNotExist:
            logger.error(
                'Parent configuration module with old_pk={} not found'.format(
                    data['parent']
                )
            )
            return

    conf_module.name = data['symbol']
    if data['department']:
        try:
            conf_module.support_team = Team.objects.get(name=data['department'])
        except Team.DoesNotExist:
            logger.warning('Team {} not found'.format(data['department']))
    conf_module.save()
    if creating:
        ImportedObjects.create(conf_module, data['id'])
    logger.info('Synced configuration module {}'.format(conf_module))


@sync_subscriber(topic='sync_venture_role_to_ralph3')
def sync_venture_role_to_ralph3(data):
    """
    Receive data about venture role from Ralph2 (ConfigurationClass in Ralph3).

    Supported fields:
    * symbol
    * parent
    * team
    """
    creating = False
    try:
        conf_class = ImportedObjects.get_object_from_old_pk(
            ConfigurationClass, data['id']
        )
    except ImportedObjectDoesNotExist:
        creating = True
        conf_class = ConfigurationClass()
        logger.info(
            'Configuration class {} ({}) not found - creating new one'.format(
                data['name'], data['id']
            )
        )

    try:
        conf_class.module = ImportedObjects.get_object_from_old_pk(
            ConfigurationModule, data['venture']
        )
    except ImportedObjectDoesNotExist:
        logger.error(
            'Venture with old_pk={} not found for role {}'.format(
                data['venture'], data['id']
            )
        )
        return

    conf_class.class_name = data['name']
    conf_class.save()
    if creating:
        ImportedObjects.create(conf_class, data['id'])
    logger.info('Synced configuration class {}'.format(conf_class))
