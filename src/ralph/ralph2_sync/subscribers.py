# -*- coding: utf-8 -*-
import logging
from contextlib import ExitStack
from functools import wraps

import pyhermes
from django.conf import settings
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
from ralph.data_center.models import (
    BaseObjectCluster,
    Cluster,
    ClusterStatus,
    ClusterType,
    DataCenter,
    DataCenterAsset,
    Rack
)
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldTypes
from ralph.networks.models import (
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)
from ralph.networks.models.choices import IPAddressStatus
from ralph.ralph2_sync.helpers import WithSignalDisabled
from ralph.ralph2_sync.publishers import (
    sync_configuration_class_to_ralph2,
    sync_configuration_module_to_ralph2,
    sync_dc_asset_to_ralph2
)
from ralph.virtual.models import (
    VirtualServer,
    VirtualServerStatus,
    VirtualServerType
)

logger = logging.getLogger(__name__)

model_mapping = {
    'Asset': DataCenterAsset,
    'AssetModel': AssetModel,
    'Rack': Rack,
    'Venture': ConfigurationModule,
    'VentureRole': ConfigurationClass,
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


def _get_service_env(data, service_key='service', env_key='environment'):
    """
    Return service-env instance based on data dict.
    """
    if service_key not in data and env_key not in data:
        return None
    service = data[service_key]
    environment = data[env_key]
    if not service or not environment:
        return None
    service_env = ServiceEnvironment.objects.get(
        service__uid=service,
        environment=ImportedObjects.get_object_from_old_pk(
            Environment, environment
        )
    )
    return service_env


def _get_configuration_path_from_venture_role(venture_role_id):
    if venture_role_id is None:
        return
    try:
        return ImportedObjects.get_object_from_old_pk(
            ConfigurationClass, venture_role_id
        )
    except ImportedObjectDoesNotExist:
        logger.error('VentureRole {} not found when syncing'.format(
            venture_role_id
        ))
    return None


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
                except Exception as e:
                    logger.exception(
                        'Exception during syncing {}'.format(str(e))
                    )
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
    * custom_fields
    """
    dca = ImportedObjects.get_object_from_old_pk(DataCenterAsset, data['id'])
    if 'hostname' in data:
        dca.hostname = data['hostname']
    if 'management_ip' in data:
        management_ip = data['management_ip']
        if management_ip:
            try:
                ip = IPAddress.objects.get(address=management_ip)
            except IPAddress.DoesNotExist:
                dca.management_ip = management_ip
            else:
                ip.ethernet.base_object = dca
                ip.ethernet.save()
                ip.is_management = True
                ip.save()
            dca.management_hostname = data.get('management_hostname')
        else:
            del dca.management_ip
    if 'service' in data and 'environment' in data:
        dca.service_env = _get_service_env(data)
    if 'venture_role' in data:
        dca.configuration_path = _get_configuration_path_from_venture_role(
            venture_role_id=data['venture_role']
        )
    dca.save()
    if 'custom_fields' in data:
        for field, value in data['custom_fields'].items():
            dca.update_custom_field(field, value)


@sync_subscriber(
    topic='sync_role_property_to_ralph3',
)
def sync_custom_fields_to_ralph3(data):
    """
    Receive data about custom fields from Ralph2

    Supported fields:
    * name (old symbol)
    * choices
    * default value
    """
    cf, _ = CustomField.objects.get_or_create(name=data['symbol'])
    if data['choices']:
        cf.type = CustomFieldTypes.CHOICE
        cf.choices = '|'.join(data['choices'])
    else:
        cf.type = CustomFieldTypes.STRING
    cf.default_value = data['default']
    cf.save()


@sync_subscriber(
    topic='sync_venture_to_ralph3',
    disable_publishers=[
        sync_configuration_class_to_ralph2,
        sync_configuration_module_to_ralph2,
    ],
)
def sync_venture_to_ralph3(data):
    """
    Receive data about venture from Ralph2 (ConfigurationModule in Ralph3).

    Supported fields:
    * name (old symbol)
    * parent (old parent)
    * team (old department)
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


@sync_subscriber(
    topic='sync_venture_role_to_ralph3',
    disable_publishers=[sync_configuration_class_to_ralph2]
)
def sync_venture_role_to_ralph3(data):
    """
    Receive data about venture role from Ralph2 (ConfigurationClass in Ralph3).

    Supported fields:
    * name (old symbol)
    * module (old venture)
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


def _get_obj(model_class, obj_id, creating=False):
    """
    Custom get or create based on imported objects.
    """
    try:
        obj = ImportedObjects.get_object_from_old_pk(
            model_class, obj_id
        )
        return obj, False
    except ImportedObjectDoesNotExist:
        obj = None
        if creating:
            obj = model_class()
        logger.info(
            '{} class ({}) not found'.format(
                model_class, obj_id
            )
        )
        return obj, True


@sync_subscriber(topic='sync_virtual_server_to_ralph3')
def sync_virtual_server_to_ralph3(data):
    virtual_type = settings.RALPH2_RALPH3_VIRTUAL_SERVER_TYPE_MAPPING.get(data['type'])  # noqa
    if virtual_type is None:
        logger.info(
            'Type {} not found in mapping dict'.format(
                data['type']
            )
        )
        virtual_type = data['type']
    virtual_server, created = _get_obj(VirtualServer, data['id'], creating=True)
    service_env = _get_service_env(data)
    virtual_server.sn = data['sn']
    virtual_server.status = VirtualServerStatus.used
    virtual_server.hostname = data['hostname']
    virtual_server.service_env = service_env
    virtual_server.configuration_path = _get_configuration_path_from_venture_role(  # noqa
        venture_role_id=data['venture_role']
    )
    virtual_server.type = VirtualServerType.objects.get_or_create(
        name=virtual_type
    )[0]
    hypervisor, _ = _get_obj(DataCenterAsset, data['parent_id'])
    virtual_server.parent = hypervisor
    virtual_server.save()
    if 'custom_fields' in data:
        for field, value in data['custom_fields'].items():
            virtual_server.update_custom_field(field, value)
    if created:
        ImportedObjects.create(virtual_server, data['id'])


@sync_subscriber(topic='sync_network_to_ralph3')
def sync_network_to_ralph3(data):
    net, created = _get_obj(Network, data['id'], creating=True)
    net.name = data['name']
    net.address = data['address']
    net.remarks = data['remarks']
    net.vlan = data['vlan']
    net.dhcp_broadcast = data['dhcp_broadcast']
    if data['reserved_ips']:
        for ip in data['reserved_ips']:
            IPAddress.objects.update_or_create(
                address=ip,
                defaults=dict(status=IPAddressStatus.reserved, network=net)
            )
    if 'gateway' in data:
        if data['gateway']:
            IPAddress.objects.filter(
                network=net,
                is_gateway=True
            ).delete()
            IPAddress.objects.update_or_create(
                address=data['gateway'],
                defaults=dict(
                    network=net,
                    is_gateway=True
                )
            )
        else:
            IPAddress.objects.filter(
                network=net,
                is_gateway=True
            ).delete()
    net.network_environment = _get_obj(
        NetworkEnvironment, data['environment_id']
    )[0]
    net.kind = _get_obj(NetworkKind, data['kind_id'])[0]
    net.save()
    if created:
        ImportedObjects.create(net, data['id'])


@sync_subscriber(topic='sync_network_kind_to_ralph3')
def sync_network_kind_to_ralph3(data):
    kind, created = _get_obj(NetworkKind, data['id'], creating=True)
    kind.name = data['name']
    kind.save()
    if created:
        ImportedObjects.create(kind, data['id'])


@sync_subscriber(topic='sync_network_environment_to_ralph3')
def sync_network_environment_to_ralph3(data):
    env, created = _get_obj(NetworkEnvironment, data['id'], creating=True)
    env.name = data['name']
    if 'data_center_id' in data:
        env.data_center = _get_obj(DataCenter, data['data_center_id'])[0]
    env.domain = data['domain']
    env.remarks = data['remarks']
    if created:
        env.hostname_template_prefix = data['hostname_template_prefix']
        env.hostname_template_counter_length = data['hostname_template_counter_length']  # noqa
        env.hostname_template_postfix = data['hostname_template_postfix']
    env.save()
    if created:
        ImportedObjects.create(env, data['id'])


@sync_subscriber(topic='sync_stacked_switch_to_ralph3')
def sync_stacked_switch_to_ralph3(data):
    stacked_switch, created = _get_obj(Cluster, data['id'], creating=True)
    service_env = _get_service_env(data)
    stacked_switch.type = ClusterType.objects.get_or_create(
        name=data['type'], defaults=dict(show_master_summary=True)
    )[0]
    stacked_switch.status = ClusterStatus.in_use
    stacked_switch.hostname = data['hostname']
    stacked_switch.service_env = service_env
    stacked_switch.configuration_path = _get_configuration_path_from_venture_role(  # noqa
        venture_role_id=data['venture_role']
    )
    stacked_switch.save()
    if 'custom_fields' in data:
        for field, value in data['custom_fields'].items():
            stacked_switch.update_custom_field(field, value)
    if 'child_devices' in data:
        for child_data in data['child_devices']:
            child, _ = _get_obj(DataCenterAsset, child_data['asset_id'])
            BaseObjectCluster.objects.update_or_create(
                cluster=stacked_switch,
                base_object=child,
                defaults=dict(
                    is_master=child_data.get('is_master', False),
                )
            )
    if created:
        ImportedObjects.create(stacked_switch, data['id'])
