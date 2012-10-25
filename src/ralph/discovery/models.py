#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovery models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models_device import (
        Device, ReadOnlyDevice, DeviceType, DeviceModel, DeviceModelGroup,
        MarginKind, DeprecationKind, LoadBalancerVirtualServer,
        LoadBalancerPool, LoadBalancerMember, Warning, SERIAL_BLACKLIST,
        DISK_VENDOR_BLACKLIST, DISK_PRODUCT_BLACKLIST
)
from ralph.discovery.models_network import (
        IPAddress, Network, DataCenter, NetworkTerminator, IPAlias, NetworkKind
    )
from ralph.discovery.models_component import (
        ComponentType, EthernetSpeed, ComponentModel, ComponentModelGroup,
        GenericComponent, DiskShare, DiskShareMount, Processor, Memory,
        Storage, FibreChannel, Ethernet, Software, SplunkUsage, OperatingSystem,
        MAC_PREFIX_BLACKLIST,
    )
from ralph.discovery.models_history import HistoryChange, HistoryCost

__all__ = [
    IPAddress,
    Network,
    DataCenter,
    NetworkTerminator,
    IPAlias,
    NetworkKind,
    MAC_PREFIX_BLACKLIST,

    ComponentType,
    EthernetSpeed,
    ComponentModel,
    ComponentModelGroup,
    GenericComponent,
    DiskShare,
    DiskShareMount,
    Processor,
    Memory,
    Storage,
    FibreChannel,
    Ethernet,
    Software,
    SplunkUsage,
    OperatingSystem,

    Device,
    ReadOnlyDevice,
    DeviceType,
    DeviceModel,
    DeviceModelGroup,
    MarginKind,
    DeprecationKind,
    LoadBalancerVirtualServer,
    LoadBalancerPool,
    LoadBalancerMember,
    Warning,
    SERIAL_BLACKLIST,
    DISK_VENDOR_BLACKLIST,
    DISK_PRODUCT_BLACKLIST,

    HistoryChange,
    HistoryCost,
]

# Load the plugins code
import ralph.discovery.plugins
