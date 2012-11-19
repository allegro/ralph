#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovery models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models_device import (
    DISK_PRODUCT_BLACKLIST, DISK_VENDOR_BLACKLIST, DeprecationKind, Device,
    DeviceModel, DeviceModelGroup, DeviceType, LoadBalancerMember,
    LoadBalancerPool, LoadBalancerVirtualServer, MarginKind, ReadOnlyDevice,
    SERIAL_BLACKLIST, Warning,
)
from ralph.discovery.models_network import (
    IPAddress, Network, DataCenter, NetworkTerminator, IPAlias, NetworkKind,
    DiscoveryQueue,
)
from ralph.discovery.models_component import (
    ComponentModel, ComponentModelGroup, ComponentType, DiskShare,
    DiskShareMount, Ethernet, EthernetSpeed, FibreChannel, GenericComponent,
    MAC_PREFIX_BLACKLIST, Memory, OperatingSystem, Processor, Software,
    SplunkUsage, Storage,
)
from ralph.discovery.models_history import HistoryChange, HistoryCost

__all__ = [
    DataCenter,
    DiscoveryQueue,
    IPAddress,
    IPAlias,
    MAC_PREFIX_BLACKLIST,
    Network,
    NetworkKind,
    NetworkTerminator,

    ComponentModel,
    ComponentModelGroup,
    ComponentType,
    DiskShare,
    DiskShareMount,
    Ethernet,
    EthernetSpeed,
    FibreChannel,
    GenericComponent,
    Memory,
    OperatingSystem,
    Processor,
    Software,
    SplunkUsage,
    Storage,

    DISK_PRODUCT_BLACKLIST,
    DISK_VENDOR_BLACKLIST,
    DeprecationKind,
    Device,
    DeviceModel,
    DeviceModelGroup,
    DeviceType,
    LoadBalancerMember,
    LoadBalancerPool,
    LoadBalancerVirtualServer,
    MarginKind,
    ReadOnlyDevice,
    SERIAL_BLACKLIST,
    Warning,

    HistoryChange,
    HistoryCost,
]

# Load the plugins code
import ralph.discovery.plugins  # noqa
