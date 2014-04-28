#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import DeviceType, ComponentType
from ralph.cmdb.models import CIOwnershipType


DEVICE_ICONS = {
    DeviceType.rack.id: 'fugue-media-player-phone',
    DeviceType.blade_system.id: 'fugue-servers',
    DeviceType.management.id: 'fugue-system-monitor',
    DeviceType.power_distribution_unit.id: 'fugue-socket',
    DeviceType.data_center.id: 'fugue-building',

    DeviceType.switch.id: 'fugue-network-hub',
    DeviceType.switch_stack.id: 'fugue-network-hub',
    DeviceType.router.id: 'fugue-application-network',
    DeviceType.load_balancer.id: 'fugue-balance',
    DeviceType.firewall.id: 'fugue-network-firewall',
    DeviceType.smtp_gateway.id: 'fugue-mails',
    DeviceType.appliance.id: 'fugue-service-bell',

    DeviceType.rack_server.id: 'fugue-computer',
    DeviceType.blade_server.id: 'fugue-server-medium',
    DeviceType.virtual_server.id: 'fugue-server-cast',
    DeviceType.cloud_server.id: 'fugue-weather-cloud',

    DeviceType.storage.id: 'fugue-database',
    DeviceType.fibre_channel_switch.id: 'fugue-drive-network',

    DeviceType.unknown.id: 'fugue-wooden-box',
    None: 'fugue-prohibition-button',
    'Linux': 'fugue-animal-penguin',
    'Windows': 'fugue-windows',
    'SunOs': 'fugue-weather',
    'Mac': 'fugue-mac-os',
    'Deleted': 'fugue-skull',
}

COMPONENT_ICONS = {
    ComponentType.processor.id: 'fugue-processor',
    ComponentType.memory.id: 'fugue-memory',
    ComponentType.disk.id: 'fugue-drive',
    ComponentType.ethernet.id: 'fugue-network-ethernet',
    ComponentType.expansion.id: 'fugue-graphic-card',
    ComponentType.fibre.id: 'fugue-drive-network',
    ComponentType.share.id: 'fugue-database-share',

    ComponentType.unknown.id: 'fugue-box',

    ComponentType.management.id: 'fugue-system-monitor',
    ComponentType.power.id: 'fugue-power-supply',
    ComponentType.cooling.id: 'fugue-thermometer-low',
    ComponentType.media.id: 'fugue-keyboard-full',
    ComponentType.chassis.id: 'fugue-wooden-box',
    ComponentType.backup.id: 'fugue-lifebuoy',
    ComponentType.software.id: 'fugue-disc',
    ComponentType.os.id: 'fugue-application-terminal',
    None: 'fugue-prohibition-button',
    'Linux': 'fugue-animal-penguin',
    'Windows': 'fugue-windows',
    'SunOs': 'fugue-weather',
    'Mac': 'fugue-mac-os',
    'Firmware': 'fugue-game',
}

OWNER_ICONS = {
    CIOwnershipType.technical.id: 'fugue-user-worker',
    CIOwnershipType.business.id: 'fugue-user-business',
    None: 'fugue-user-nude',
}


def get_device_model_icon(model):
    if model is None:
        return DEVICE_ICONS[None]
    return DEVICE_ICONS[model.type]


def get_device_icon(device):
    if device is None or device.model is None:
        return DEVICE_ICONS[None]
    if device.deleted:
        return DEVICE_ICONS['Deleted']
    return (DEVICE_ICONS.get(device.model.name) or
            DEVICE_ICONS.get(device.model.type) or
            DEVICE_ICONS[None])


def get_component_model_icon(model):
    if model is None:
        return COMPONENT_ICONS[None]
    return COMPONENT_ICONS.get(model.family) or COMPONENT_ICONS[model.type]


def get_component_icon(component):
    if component is None or component.model is None:
        return COMPONENT_ICONS[None]
    return get_component_model_icon(component.model)


def get_venture_icon(venture):
    if venture and venture.department and venture.department.icon is not None:
        return 'fugue-%s' % venture.department.icon.name.replace('_', '-')
    if venture.is_infrastructure:
        return 'fugue-hard-hat'
    if not venture.show_in_ralph:
        return 'fugue-store-market-stall'
    return 'fugue-store'


def get_owner_icon(owner):
    if owner is None:
        return OWNER_ICONS[None]
    return OWNER_ICONS.get(owner.type) or OWNER_ICONS[None]


def get_network_icon(net):
    icon = 'fugue-network'
    if net and net.kind and net.kind.icon:
        icon = net.kind.icon
    return icon
