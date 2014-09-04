#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovery models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models_device import (
    Connection,
    ConnectionType,
    DeprecationKind,
    Device,
    DeviceModel,
    DeviceType,
    DISK_PRODUCT_BLACKLIST,
    DISK_VENDOR_BLACKLIST,
    LoadBalancerMember,
    LoadBalancerPool,
    LoadBalancerVirtualServer,
    MarginKind,
    NetworkConnection,
    ReadOnlyDevice,
    SERIAL_BLACKLIST,
    UptimeSupport,
)
from ralph.discovery.models_network import (
    DataCenter,
    DiscoveryQueue,
    Environment,
    IPAddress,
    IPAlias,
    Network,
    NetworkKind,
    NetworkTerminator,
)
from ralph.discovery.models_component import (
    ComponentModel,
    ComponentType,
    DiskShare,
    DiskShareMount,
    Ethernet,
    EthernetSpeed,
    FibreChannel,
    GenericComponent,
    MAC_PREFIX_BLACKLIST,
    Memory,
    OperatingSystem,
    Processor,
    Software,
    SplunkUsage,
    Storage,
)
from ralph.discovery.models_history import (
    DiscoveryValue,
    DiscoveryWarning,
    HistoryChange,
    HistoryCost,
)


__all__ = [
    'DataCenter',
    'DiscoveryQueue',
    'Environment',
    'IPAddress',
    'IPAlias',
    'MAC_PREFIX_BLACKLIST',
    'Network',
    'NetworkKind',
    'NetworkTerminator',

    'ComponentModel',
    'ComponentType',
    'DiskShare',
    'DiskShareMount',
    'Ethernet',
    'EthernetSpeed',
    'FibreChannel',
    'GenericComponent',
    'Memory',
    'OperatingSystem',
    'Processor',
    'Software',
    'SplunkUsage',
    'Storage',

    'DISK_PRODUCT_BLACKLIST',
    'DISK_VENDOR_BLACKLIST',
    'DeprecationKind',
    'Device',
    'DeviceModel',
    'DeviceType',
    'Connection',
    'ConnectionType',
    'LoadBalancerMember',
    'LoadBalancerPool',
    'LoadBalancerVirtualServer',
    'MarginKind',
    'NetworkConnection',
    'ReadOnlyDevice',
    'SERIAL_BLACKLIST',
    'UptimeSupport',

    'HistoryChange',
    'HistoryCost',
    'DiscoveryValue',
    'DiscoveryWarning',

]

# Load the plugins code
import ralph.discovery.plugins  # noqa
