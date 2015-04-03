# -*- coding: utf-8 -*-

"""
Translating between the device database model and the scan data. Also making
diff between data from DB and merged results from all plugins.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import IntegrityError
from django.db import models as db
from django.conf import settings

from ralph.discovery.models_component import (
    ComponentModel,
    ComponentType,
    DiskShare,
    DiskShareMount,
    Ethernet,
    FibreChannel,
    GenericComponent,
    Memory,
    OperatingSystem,
    Processor,
    Storage,
    Software,
)
from ralph.discovery.models_network import (
    IPAddress,
)
from ralph.discovery.models_device import (
    Connection,
    ConnectionType,
    Device,
    DeviceModel,
    DeviceType,
    NetworkConnection,
)
from ralph.scan.merger import merge as merge_component
from ralph.scan.util import get_asset_by_name
from ralph_assets.models import Asset


# For every fields here merger tries join data using this pairs of keys.
UNIQUE_FIELDS_FOR_MERGER = {
    'disks': [('serial_number',), ('device', 'mount_point')],
    'processors': [('device', 'index')],
    'memory': [('device', 'index')],
    'fibrechannel_cards': [('physical_id', 'device')],
    'parts': [('serial_number',)],
    'disk_exports': [('serial_number',)],
    'disk_shares': [('device', 'serial_number')],
    'installed_software': [('device', 'path')],
}
SAVE_PRIORITY = 215


def has_logical_children(device):
    """Returns True if this device has logical children or False if it has
    physical ones."""
    return device.model and device.model.type in (DeviceType.switch_stack,)


def get_choice_by_name(choices, name):
    """
    Find choices by name (with spaces or without spaces) or by raw_name.
    """

    try:
        return choices.from_name(name.replace(' ', '_').lower())
    except ValueError:
        for choice_id, choice_name in choices():
            choice = choices.from_id(choice_id)
            if choice.raw == name:
                return choice
        raise


def _update_addresses(device, address_data, is_management=False):
    """
    Update management or system ip addresses of a device based on data.

    :param device: Device to be updated
    :param address_data: list of strings with the ip addresses
    :param is_management: whether to update management or system addresses
    """
    ipaddress_ids = []
    for ip in address_data:
        try:
            ipaddress = IPAddress.objects.get(address=ip)
        except IPAddress.DoesNotExist:
            ipaddress = IPAddress(address=ip)
        ipaddress.device = device
        ipaddress.is_management = is_management
        ipaddress.save(update_last_seen=False)
        ipaddress_ids.append(ipaddress.id)
    # Disconnect the rest of addresses from this device
    for ipaddress in IPAddress.objects.filter(
        device=device,
        is_management=is_management,
    ).exclude(id__in=ipaddress_ids):
        ipaddress.device = None
        ipaddress.save(update_last_seen=False)


def _get_or_create_model_for_component(
    model_type,
    component_data,
    field_map,
    forbidden_model_fields=set(),
    save_priority=SAVE_PRIORITY,
):
    """
    For concrete component type try to save or reuse instance of
    Component using field_map and list of fields to save.
    Field_map maps from component fields to database fields. Some of the
    fields are forbidden to save for given component type, for example field
    name is forbidden in Storage Component.

    :param model_type: If provided, a 'model' field will be added
    :param component_data: list of dicts describing the components
    :param field_map: mapping from database fields to component_data keys
    :param forbidden_model_fields: If provided, model will be created
                                   without those fields
    :param save_priority: Save priority
    """
    model_fields = {
        field: component_data[field_map[field]]
        for field in field_map
        if all((
            component_data.get(field_map[field]),
            field != 'type',
            field not in forbidden_model_fields,
        ))
    }
    if all((
        'model_name' in component_data,
        'name' not in forbidden_model_fields,
    )):
        model_fields['name'] = component_data['model_name']
    if model_type == ComponentType.software:
        path = model_fields.get('path')
        family = model_fields.get('family')
        if path and not family:
            model_fields['family'] = path
    if 'family' in model_fields:
        model_fields['family'] = model_fields.get('family', '')[:128]
    model, created = ComponentModel.create(
        model_type,
        save_priority,
        **model_fields)
    return model


def _update_component_data(
    device,
    component_data,
    Component,
    field_map,
    unique_fields,
    model_type=None,
    forbidden_model_fields=set(),
    save_priority=SAVE_PRIORITY,
):
    """
    Update components of a device based on the data from scan.

    This function is a little tricky, because we want to reuse the
    components as much as possible, instead of deleting everything and
    creating new ones every time.

    :param component_data: list of dicts describing the components
    :param Component: model to use to query and create components
    :param field_map: mapping from database fields to component_data keys
    :param unique_fields: list of tuples of fields that are unique together
    :param model_type: If provided, a 'model' field will be added
    :param forbidden_model_fields: If provided, model will be created
                                   without those fields
    :param save_priority: Save priority
    """

    component_ids = []
    for index, data in enumerate(component_data):
        model = None
        data['device'] = device
        data['index'] = index
        component = None
        for group in unique_fields:
            # First try to find an existing component using unique fields
            fields = {
                field: data[field_map[field]]
                for field in group
                if data.get(field_map[field]) is not None
            }
            if len(group) != len(fields):
                continue
            try:
                component_to_update = Component.objects.get(**fields)
            except Component.DoesNotExist:
                continue
            else:
                if not component:
                    component = component_to_update
                else:
                    if component.id != component_to_update.id:
                        component_to_update.delete()
        if not component:
            # No matching component found, create a new one
            if model_type is not None or 'type' in data:
                # If model_type is provided, create the model
                if model_type is None:
                    try:
                        model_type = get_choice_by_name(
                            ComponentType,
                            data['type']
                        )
                    except ValueError:
                        model_type = None
                if model_type is not None:
                    # family is required for disks
                    if model_type == ComponentType.disk:
                        if 'family' not in data or not data['family']:
                            data['family'] = 'Generic disk'
                    model = _get_or_create_model_for_component(
                        model_type,
                        data,
                        field_map,
                        forbidden_model_fields,
                        save_priority=save_priority,
                    )
                if model is None:
                    raise ValueError('Unknown model')
                component = Component(model=model)
            else:
                component = Component()
        # Fill the component with values from the data dict
        for field, key in field_map.iteritems():
            if key in data:
                setattr(component, field, data[key])
        if model_type is not None and model is None:
            try:
                model = _get_or_create_model_for_component(
                    model_type,
                    data,
                    field_map,
                    forbidden_model_fields,
                    save_priority=save_priority,
                )
            except AssertionError:
                pass
            else:
                if model:
                    component.model = model
        component.save(priority=save_priority)
        component_ids.append(component.id)
    # Delete the components that are no longer current
    for component in Component.objects.filter(
        device=device,
    ).exclude(
        id__in=component_ids,
    ):
        component.delete()


def get_device_data(device):
    """
    Generate a dict with all information that is stored in the database
    about this device, in a format compatible with that returned by the
    discovery plugins.
    """

    data = {
        'id': device.id,
        'system_ip_addresses': [
            ip.address for ip in
            device.ipaddress_set.filter(is_management=False)
        ],
        'management_ip_addresses': [
            ip.address for ip in
            device.ipaddress_set.filter(is_management=True)
        ],
        'mac_addresses': [
            eth.mac for eth in device.ethernet_set.all()
        ],
    }
    if device.name != 'unknown':
        data['hostname'] = device.name
    if device.model is not None:
        data['model_name'] = device.model.name
        data['type'] = DeviceType.from_id(device.model.type).raw
    if device.sn is not None:
        data['serial_number'] = device.sn
    if device.chassis_position:
        data['chassis_position'] = device.chassis_position
    if device.dc:
        data['data_center'] = device.dc
    if device.rack:
        data['rack'] = device.rack
    if device.management:
        data['management'] = device.management.address
    data['memory'] = [
        {
            'label': m.label,
            'size': m.size,
            'speed': m.speed,
            'index': m.index,
        } for m in device.memory_set.order_by('index')
    ]
    data['processors'] = [
        {
            'model_name': p.model.name if p.model else '',
            'speed': p.speed,
            'cores': p.get_cores(),
            'family': p.model.family if p.model else '',
            'label': p.label,
            'index': p.index,
        } for p in device.processor_set.order_by('index')
    ]
    disks = []
    for disk in device.storage_set.order_by('sn', 'mount_point'):
        disk_data = {
            'label': disk.label,
            'size': disk.size,
        }
        if disk.sn:
            disk_data['serial_number'] = disk.sn
        if disk.mount_point:
            disk_data['mount_point'] = disk.mount_point
        if disk.model:
            disk_data.update({
                'model_name': disk.model.name,
                'family': disk.model.family,
            })
        disks.append(disk_data)
    data['disks'] = disks
    data['disk_exports'] = [
        {
            'serial_number': share.wwn,
            'full': share.full,
            'size': share.size,
            'snapshot_size': share.snapshot_size,
            'label': share.label,
            'share_id': share.share_id,
            'model_name': share.model.name if share.model else '',
        } for share in device.diskshare_set.order_by('wwn')
    ]
    disk_shares = []
    for mount in device.disksharemount_set.order_by('volume', 'address'):
        mount_data = {
            'serial_number': mount.share.wwn if mount.share else '',
            'size': mount.size,
            'address': mount.address.address if mount.address else '',
            'is_virtual': mount.is_virtual,
            'volume': mount.volume,
        }
        if mount.server:
            mount_data['server'] = {
                'serial_number': mount.server.sn,
            }
        else:
            mount_data['server'] = None
        disk_shares.append(mount_data)
    data['disk_shares'] = disk_shares
    data['installed_software'] = [
        {
            'label': soft.label,
            'version': soft.version,
            'path': soft.path,
            'serial_number': soft.sn,
            'model_name': soft.model.name if soft.model else '',
        } for soft in device.software_set.order_by('label', 'version')
    ]
    data['fibrechannel_cards'] = [
        {
            'physical_id': fc.physical_id,
            'label': fc.label,
            'model_name': fc.model.name if fc.model else '',
        } for fc in device.fibrechannel_set.order_by('label')
    ]
    data['parts'] = [
        {
            'serial_number': part.sn,
            'label': part.label,
            'boot_firmware': part.boot_firmware,
            'hard_firmware': part.hard_firmware,
            'diag_firmware': part.diag_firmware,
            'mgmt_firmware': part.mgmt_firmware,
            'model_name': part.model.name if part.model else '',
            'type': ComponentType.from_id(
                part.model.type,
            ).raw if part.model else '',
        } for part in device.genericcomponent_set.order_by('sn')
    ]
    if has_logical_children(device):
        data['subdevices'] = [
            get_device_data(dev)
            for dev in device.logicalchild_set.order_by('id')
        ]
    else:
        data['subdevices'] = [
            get_device_data(dev)
            for dev in device.child_set.order_by('id')
        ]
    if device.operatingsystem_set.exists():
        system = device.operatingsystem_set.all()[0]
        data['system_label'] = system.label
        data['system_memory'] = system.memory
        data['system_storage'] = system.storage
        data['system_cores_count'] = system.cores_count
        if system.model:
            data['system_family'] = system.model.family
    connections = []
    for conn in device.outbound_connections.filter(inbound__deleted=False):
        connected_device_sn = ''
        if conn.inbound.sn is not None:
            connected_device_sn = conn.inbound.sn
        connection_details = {}
        if conn.connection_type == ConnectionType.network:
            try:
                network_connection_details = NetworkConnection.objects.get(
                    connection=conn
                )
            except NetworkConnection.DoesNotExist:
                pass
            else:
                connection_details[
                    'outbound_port'
                ] = network_connection_details.outbound_port
                connection_details[
                    'inbound_port'
                ] = network_connection_details.inbound_port
        connections.append({
            'connection_type': ConnectionType.name_from_id(
                conn.connection_type
            ),
            'connected_device_mac_addresses': ",".join([
                mac.mac for mac in conn.inbound.ethernet_set.all()
            ]),
            'connected_device_ip_addresses': ",".join([
                ip.address for ip in conn.inbound.ipaddress_set.all()
            ]),
            'connected_device_serial_number': connected_device_sn,
            'connection_details': connection_details
        })
    data['connections'] = connections
    if 'ralph_assets' in settings.INSTALLED_APPS:
        from ralph_assets.api_ralph import get_asset
        asset = get_asset(device.id)
        if asset:
            data['asset'] = '{} - {} - {}'.format(asset['model'],
                                                  asset['sn'],
                                                  asset['barcode'])
        else:
            data['asset'] = None
    return data


def check_if_can_edit_position(data):
    asset = data.get('asset')
    if not asset:
        return True
    if not isinstance(asset, Asset):
        asset = get_asset_by_name(asset)
        if not asset:
            return True
    return False


def set_device_data(device, data, save_priority=SAVE_PRIORITY, warnings=[]):
    """
    Go through the submitted data, and update the Device object
    in accordance with the meaning of the particular fields.
    """

    keys = {
        'sn': 'serial_number',
        'name': 'hostname',
        'dc': 'data_center',
        'rack': 'rack',
        'barcode': 'barcode',
        'chassis_position': 'chassis_position',
    }
    can_edit_position = check_if_can_edit_position(data)
    for field_name, key_name in keys.iteritems():
        if key_name in data:
            if all((
                not can_edit_position,
                field_name in ('dc', 'rack', 'chassis_position'),
            )):
                warnings.append(
                    'You can not set data for `{}` here - skipped. Use assets '
                    'module.'.format(key_name),
                )
                continue
            setattr(device, field_name, data[key_name])
    if 'model_name' in data and (data['model_name'] or '').strip():
        try:
            model_type = get_choice_by_name(
                DeviceType,
                data.get('type', 'unknown')
            )
        except ValueError:
            model_type = DeviceType.unknown
        try:
            # Don't use get_or_create, because we are in transaction
            device.model = DeviceModel.objects.get(
                name=data['model_name'],
                type=model_type,
            )
        except DeviceModel.DoesNotExist:
            model = DeviceModel(
                name=data['model_name'],
                type=model_type,
            )
            try:
                model.save()
            except IntegrityError:
                if model_type != DeviceType.unknown:
                    try:
                        device.model = DeviceModel.objects.get(
                            name='%s (%s)' % (
                                data['model_name'], model_type.raw
                            ),
                            type=model_type,
                        )
                    except DeviceModel.DoesNotExist:
                        model = DeviceModel(
                            type=model_type,
                            name='%s (%s)' % (
                                data['model_name'], model_type.raw
                            ),
                        )
                        try:
                            model.save()
                        except IntegrityError:
                            pass
                        else:
                            device.model = model
            else:
                device.model = model
    if 'disks' in data:
        _update_component_data(
            device,
            data['disks'],
            Storage,
            {
                'sn': 'serial_number',
                'device': 'device',
                'size': 'size',
                'speed': 'speed',
                'mount_point': 'mount_point',
                'label': 'label',
                'family': 'family',
                'model_name': 'model_name',
            },
            [
                ('sn',),
                ('device', 'mount_point'),
            ],
            ComponentType.disk,
            {'name'},
            save_priority=save_priority,
        )
    if 'processors' in data:
        for index, processor in enumerate(data['processors']):
            processor['index'] = index
        _update_component_data(
            device,
            data['processors'],
            Processor,
            {
                'device': 'device',
                'label': 'label',
                'speed': 'speed',
                'cores': 'cores',
                'family': 'family',
                'index': 'index',
                'model_name': 'model_name',
            },
            [
                ('device', 'index'),
            ],
            ComponentType.processor,
            save_priority=save_priority,
        )
    if 'memory' in data:
        for index, memory in enumerate(data['memory']):
            memory['index'] = index
            memory['speed'] = memory.get('speed', None) or None
        _update_component_data(
            device,
            data['memory'],
            Memory,
            {
                'device': 'device',
                'label': 'label',
                'speed': 'speed',
                'size': 'size',
                'index': 'index',
            },
            [
                ('device', 'index'),
            ],
            ComponentType.memory,
            {'name'},
            save_priority=save_priority,
        )
    if 'mac_addresses' in data:
        _update_component_data(
            device,
            [{'mac': mac} for mac in data['mac_addresses']],
            Ethernet,
            {
                'mac': 'mac',
                'device': 'device',
            },
            [('mac',)],
            None,
            save_priority=save_priority,
        )
    if 'management_ip_addresses' in data:
        if not data.get('asset'):
            _update_addresses(device, data['management_ip_addresses'], True)
        else:
            warnings.append(
                'Management IP addresses ({}) have been ignored. To change '
                'them, please use the Assets module.'.format(
                    ', '.join(data['management_ip_addresses']),
                ),
            )
    if 'system_ip_addresses' in data:
        _update_addresses(device, data['system_ip_addresses'], False)
    if 'management' in data:
        if not data.get('asset'):
            device.management, created = IPAddress.concurrent_get_or_create(
                address=data['management'], defaults={'is_management': True},
            )
        else:
            warnings.append(
                'Management IP address ({}) has been ignored. To change '
                'them, please use the Assets module.'.format(
                    data['management'],
                ),
            )
    if 'fibrechannel_cards' in data:
        _update_component_data(
            device,
            data['fibrechannel_cards'],
            FibreChannel,
            {
                'device': 'device',
                'label': 'label',
                'model_name': 'model_name',
                'physical_id': 'physical_id',
            },
            [
                ('physical_id', 'device'),
            ],
            ComponentType.fibre,
            save_priority=save_priority,
        )
    if 'parts' in data:
        _update_component_data(
            device,
            data['parts'],
            GenericComponent,
            {
                'device': 'device',
                'label': 'label',
                'model_name': 'model_name',
                'sn': 'serial_number',
                'type': 'type',
            },
            [
                ('sn',),
            ],
            save_priority=save_priority,
        )
    if 'disk_exports' in data:
        _update_component_data(
            device,
            data['disk_exports'],
            DiskShare,
            {
                'device': 'device',
                'label': 'label',
                'wwn': 'serial_number',
                'size': 'size',
                'full': 'full',
                'snapshot_size': 'snapshot_size',
                'share_id': 'share_id',
                'model_name': 'model_name',
            },
            [
                ('wwn',),
            ],
            ComponentType.share,
            save_priority=save_priority,
        )
    if 'disk_shares' in data:
        shares = []
        for share in data['disk_shares']:
            if share.get('server'):
                servers = find_devices({
                    'server': share['server'],
                })
                if len(servers) > 1:
                    raise ValueError(
                        "Multiple servers found for share mount %r" % share,
                    )
                elif len(servers) <= 0:
                    raise ValueError(
                        "No server found for share mount %r" % share,
                    )
                share['server'] = servers[0]
            else:
                share['server'] = None
            try:
                share['share'] = DiskShare.objects.get(
                    wwn=share['serial_number']
                )
            except DiskShare.DoesNotExist:
                warnings.append(
                    'No share found for share mount: %r' % share
                )
                continue
            if share.get('address'):
                try:
                    share['address'] = IPAddress.objects.get(
                        address=share['address'],
                    )
                except IPAddress.DoesNotExist:
                    warnings.append(
                        'No IP address found for share mount: %r' % share
                    )
                    continue
            elif 'address' in share:
                del share['address']
            shares.append(share)
        _update_component_data(
            device,
            shares,
            DiskShareMount,
            {
                'share': 'share',
                'size': 'size',
                'address': 'address',
                'is_virtual': 'is_virtual',
                'volume': 'volume',
                'server': 'server',
                'device': 'device',
            },
            [
                ('device', 'share'),
            ],
            save_priority=save_priority,
        )
    if 'installed_software' in data:
        _update_component_data(
            device,
            data['installed_software'],
            Software,
            {
                'device': 'device',
                'path': 'path',
                'label': 'label',
                'version': 'version',
                'model_name': 'model_name',
                'sn': 'serial_number',
            },
            [
                ('device', 'path'),
            ],
            ComponentType.software,
            save_priority=save_priority,
        )
    if (
        'system_label' in data or
        'system_memory' in data or
        'system_storage' in data or
        'system_cores_count' in data or
        'system_family' in data or
        'system_model_name' in data
    ):
        _update_component_data(
            device,
            [data],
            OperatingSystem,
            {
                'device': 'device',
                'memory': 'system_memory',
                'storage': 'system_storage',
                'cores_count': 'system_cores_count',
                'family': 'system_family',
                'label': 'system_label',
                'model_name': 'system_model_name',
            },
            [
                ('device',),
            ],
            ComponentType.os,
            save_priority=save_priority,
        )
    if 'subdevices' in data:
        subdevice_ids = []
        for subdevice_data in data['subdevices']:
            subdevice = device_from_data(
                subdevice_data,
                save_priority=save_priority,
                warnings=warnings
            )
            if has_logical_children(device):
                subdevice.logical_parent = device
                if subdevice.parent and subdevice.parent.id == device.id:
                    subdevice.parent = None
            else:
                subdevice.parent = device
            subdevice.save(priority=save_priority)
            subdevice_ids.append(subdevice.id)
        set_, parent_attr = (
            (device.logicalchild_set, 'logical_parent')
            if has_logical_children(device)
            else (device.child_set, 'parent')
        )
        for subdevice in set_.exclude(id__in=subdevice_ids):
            setattr(subdevice, parent_attr, None)
            subdevice.save(priority=save_priority)
    if 'connections' in data:
        parsed_connections = set()
        for connection_data in data['connections']:
            connection = connection_from_data(device, connection_data)
            if connection.connection_type == ConnectionType.network:
                connetion_details = connection_data.get('details', {})
                if connetion_details:
                    outbound_port = connetion_details.get('outbound_port')
                    inbound_port = connetion_details.get('inbound_port')
                    try:
                        details = NetworkConnection.objects.get(
                            connection=connection
                        )
                    except NetworkConnection.DoesNotExist:
                        details = NetworkConnection(connection=connection)
                    if outbound_port:
                        details.outbound_port = outbound_port
                    if inbound_port:
                        details.inbound_port = inbound_port
                    details.save()
            parsed_connections.add(connection.pk)
        device.outbound_connections.exclude(
            pk__in=parsed_connections
        ).delete()
    if 'asset' in data and 'ralph_assets' in settings.INSTALLED_APPS:
        from ralph_assets.api_ralph import assign_asset
        asset = data['asset']
        if asset and not isinstance(asset, Asset):
            asset = get_asset_by_name(asset)
        if asset:
            assign_asset(device.id, asset.id)


def connection_from_data(device, connection_data):
    query = {}
    serial_number = connection_data.get('connected_device_serial_number')
    if serial_number:
        query['sn'] = serial_number
    mac_addresses = connection_data.get('connected_device_mac_addresses')
    if mac_addresses:
        mac_addresses = [mac.strip() for mac in mac_addresses.split(",")]
        query['ethernet__mac__in'] = mac_addresses
    ip_addresses = connection_data.get('connected_device_ip_addresses')
    if ip_addresses:
        ip_addresses = [ip.strip() for ip in ip_addresses.split(",")]
        query['ipaddress__address__in'] = ip_addresses
    if not query:
        raise ValueError(
            "Can not find connected device. Please specify connected device "
            "MAC address or IP address or serial number."
        )
    connected_devices = Device.objects.filter(**query).distinct()
    if not connected_devices:
        raise ValueError(
            "Can not find connected device. Please specify connected device "
            "MAC address or IP address or serial number."
        )
    if len(connected_devices) > 1:
        raise ValueError(
            "Many devices found. Probably specified MAC addresses or "
            "IP addresses are not connected with one device..."
        )
    connected_device = connected_devices[0]
    connection_type = get_choice_by_name(
        ConnectionType,
        connection_data.get('connection_type', '')
    )
    try:
        return device.outbound_connections.get(
            inbound=connected_device,
            connection_type=connection_type
        )
    except Connection.DoesNotExist:
        return Connection.objects.create(
            outbound=device,
            inbound=connected_device,
            connection_type=connection_type
        )


def device_from_data(
    data, save_priority=SAVE_PRIORITY, user=None, warnings=[]
):
    """
    Create or find a device based on the provided scan data.
    """

    sn = data.get('serial_number')
    ethernets = [('', mac, None) for mac in data.get('mac_addresses', [])]
    model_name = data.get('model_name')
    model_type = get_choice_by_name(
        DeviceType,
        data.get('type', 'unknown')
    )
    device = Device.create(
        sn=sn,
        ethernets=ethernets,
        model_name=model_name,
        model_type=model_type,
        priority=save_priority,
    )
    set_device_data(
        device, data, save_priority=save_priority, warnings=warnings
    )
    device.save(priority=save_priority, user=user)
    return device


def merge_data(*args, **kwargs):
    """
    Merge several dicts with data from a scan into a single dict.

    :param *args: data to merge
    :param only_multiple: if True, only keys with multiple values are returned
    """

    only_multiple = kwargs.get('only_multiple', False)
    merged = {}
    for result in args:
        for plugin_name, data in result.iteritems():
            for key, value in data.get('device', {}).iteritems():
                merged.setdefault(key, {})[plugin_name] = value
    # Now, make the values unique.
    unique = {}
    required_fields = ['model_name', 'type']
    if 'ralph_assets' in settings.INSTALLED_APPS:
        required_fields.append('asset')
    for key, values in merged.iteritems():
        repeated = {}
        for source, value in values.iteritems():
            repeated.setdefault(unicode(value), []).append(source)
        if (
            only_multiple and
            len(repeated) <= 1 and
            key not in required_fields and
            'database' in values
        ):
            continue
        for value_str, sources in repeated.iteritems():
            sources.sort()
            unique.setdefault(
                key,
                {},
            )[tuple(sources)] = merged[key][sources[0]]
    return unique


def find_devices(result):
    """
    Find all devices that can be possibly matched to this scan data.
    """

    ids = set(
        r['device']['id']
        for r in result.itervalues() if 'id' in r.get('device', {})
    )
    serials = set(
        r['device']['serial_number']
        for r in result.itervalues() if 'serial_number' in r.get('device', {})
    )
    macs = set()
    for r in result.itervalues():
        macs |= set(r.get('device', {}).get('mac_addresses', []))
    return Device.admin_objects.filter(
        db.Q(id__in=ids) |
        db.Q(sn__in=serials) |
        db.Q(ethernet__mac__in=macs)
    ).distinct()


def append_merged_proposition(data, device, external_priorities={}):
    """
    Add `merged data` proposition to other Scan results.

    :param data: results from scan plugins
    :param device: device object connected with plugins results
    """

    for component, results in data.iteritems():
        if component not in UNIQUE_FIELDS_FOR_MERGER:
            continue
        # sanitize data...
        data_to_merge = {}
        for sources, plugins_data in results.iteritems():
            if 'database' in sources:
                plugin_name = 'database'
            else:
                plugin_name = sources[0]
            data_to_merge[plugin_name] = []
            for index, row in enumerate(plugins_data):
                row.update({
                    'device': device.pk,
                    'index': index,
                })
                for key, value in row.items():
                    if value is None:
                        del row[key]
                data_to_merge[plugin_name].append(row)
        merged = merge_component(
            component,
            data_to_merge,
            UNIQUE_FIELDS_FOR_MERGER[component],
            external_priorities,
        )
        if merged:
            for row in merged:
                del row['device']
            data[component][('merged',)] = merged


def get_external_results_priorities(results):
    """
    Return additional, external results priorities.

    Results priorities from external plugins (e.g. DonPedro) are coming
    together with results.
    """

    priorities = {}
    for plugin_name, plugin_results in results.iteritems():
        if 'results_priority' in plugin_results:
            priorities[plugin_name] = plugin_results['results_priority']
    return priorities
