# -*- coding: utf-8 -*-

"""
Translating between the device database model and the scan data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models_component import (
    ComponentModel,
    ComponentType,
    Ethernet,
    FibreChannel,
    Memory,
    Processor,
    Storage,
)
from ralph.discovery.models_network import (
    IPAddress,
)
from ralph.discovery.models_device import (
    Device,
    DeviceType,
    DeviceModel,
)


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


def _update_component_data(
    device,
    component_data,
    Component,
    field_map,
    unique_fields,
    model_type=None,
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
    :prarm model_type: If provided, a 'model' field will be added
    """

    component_ids = []
    for index, data in enumerate(component_data):
        data['device'] = device
        data['index'] = index
        for group in unique_fields:
            # First try to find an existing component using unique fields
            fields = {
                field: data[field_map[field]]
                for field in group
                if data.get(field_map[field]) is not None
            }
            if not fields:
                continue
            try:
                component = Component.objects.get(**fields)
            except Component.DoesNotExist:
                continue
            break
        else:
            # No matching component found, create a new one
            if model_type is not None or 'model_type' in data:
                # If model_type is provided, create the model
                model = None
                if model_type is None:
                    try:
                        model_type = ComponentType.from_name(data['model_type'])
                    except ValueError:
                        model_type = None
                if model_type is not None:
                    model_fields = {
                        field: data[field_map[field]]
                        for field in field_map
                        if data.get(field_map[field])
                    }
                    if 'model_name' in data:
                        model_fields['name'] = data['model_name']
                    model, created = ComponentModel.create(
                        model_type,
                        0,
                        **model_fields)
                if model is None:
                    raise ValueError('Unknown model')
                component = Component(model=model)
            else:
                component = Component()
        # Fill the component with values from the data dict
        for field, key in field_map.iteritems():
            if key in data:
                setattr(component, field, data[key])
        component.save()
        component_ids.append(component.id)
    # Delete the components that are no longer current
    for component in Component.objects.filter(
        device=device,
    ).exclude(
        id__in=component_ids,
    ):
        component.delete()


def get_device_data(device):
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
        if device.model.type != DeviceType.unknown:
            data['type'] = DeviceType.from_id(device.model.type).name
    if device.sn is not None:
        data['serial_number'] = device.sn
    if device.chassis_position:
        data['chassis_position'] = device.chassis_position
    if device.dc:
        data['data_center'] = device.dc
    if device.rack:
        data['rack'] = device.rack
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
    data['disk_shares'] = [
        {
            'serial_number': mount.share.wwn if mount.share else '',
            'size': mount.size,
            'address': mount.address.address if mount.address else '',
            'is_virtual': mount.is_virtual,
            'volume': mount.volume,
            'server_serial_number': mount.server.sn if mount.server else '',
        } for mount in device.disksharemount_set.order_by('volume', 'address')
    ]
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
    data['subdevices'] = [
        {
            'device': get_device_data(dev),
        } for dev in device.child_set.order_by('id')
    ]
    if device.operatingsystem_set.exists():
        system = device.operatingsystem_set.all()[0]
        data['system_label'] = system.label
        data['system_memory'] = system.memory
        data['system_storage'] = system.storage
        data['system_cores_count'] = system.cores_count
        if system.model:
            data['system_family'] = system.model.family
            data['system_model_name'] = system.model.name

    # Some details of the device are still not returned:
    # TODO asset
    return data


def set_device_data(device, data):
    """
    Go through the submitted data, and update the Device object
    in accordance with the meaning of the particular fields.
    """

    # Some details of the device are still not updated:
    # TODO parts
    # TODO disk shares
    # TODO disk exports
    # TODO installed software
    # TODO subdevices
    # TODO system
    # TODO asset

    keys = {
        'sn': 'serial_number',
        'name': 'hostname',
        'dc': 'data_center',
        'rack': 'rack',
        'barcode': 'barcode',
        'chassis_position': 'chassis_position',
    }
    for field_name, key_name in keys.iteritems():
        if key_name in data:
            setattr(device, field_name, data[key_name])
    if 'model_name' in data:
        try:
            model_type = DeviceType.from_name(data.get('type', 'unknown'))
        except ValueError:
            model_type = ComponentType.unknown
        try:
            # Don't use get_or_create, because we are in transaction
            device.model = DeviceModel.objects.get(
                type=model_type,
                name=data['model_name'],
            )
        except DeviceModel.DoesNotExist:
            model = DeviceModel(
                type=model_type,
                name=data['model_name'],
            )
            model.save()
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
        )
    if 'memory' in data:
        for index, memory in enumerate(data['memory']):
            memory['index'] = index
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
            [
                ('mac',),
            ],
            None,
        )
    if 'management_ip_addresses' in data:
        _update_addresses(device, data['management_ip_addresses'], True)
    if 'system_ip_addresses' in data:
        _update_addresses(device, data['system_ip_addresses'], False)
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
                ('physical_id',),
            ],
            ComponentType.fibre,
        )


def device_from_data(data):
    """
    Create or find a device based on the provided scan data.
    """

    sn = data.get('serial_number')
    ethernets = [('', mac, None) for mac in data.get('mac_addresses', [])]
    model_name = data.get('model_name')
    model_type = DeviceType.from_name(data.get('type', 'unknown').lower())
    device = Device.create(
        sn=sn,
        ethernets=ethernets,
        model_name=model_name,
        model_type=model_type,
    )
    set_device_data(device, data)
    device.save()
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
    for key, values in merged.iteritems():
        repeated = {}
        for source, value in values.iteritems():
            repeated.setdefault(unicode(value), []).append(source)
        if only_multiple and len(repeated) <= 1:
            continue
        for value_str, sources in repeated.iteritems():
            sources.sort()
            unique.setdefault(
                key,
                {},
            )[tuple(sources)] = merged[key][sources[0]]
    return unique
