# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service
)
from ralph.assets.models.components import (
    ComponentModel,
    GenericComponent
)
from ralph.assets.models.networks import (
    Network,
    NetworkEnvironment,
    NetworkKind,
    NetworkTerminator,
    DiscoveryQueue,
    IPAddress,
)


@admin.register(Service)
class ServiceAdmin(reversion.VersionAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerAdmin(reversion.VersionAdmin):
    pass


@admin.register(Environment)
class EnvironmentAdmin(reversion.VersionAdmin):
    pass


@admin.register(AssetModel)
class AssetModelAdmin(reversion.VersionAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(reversion.VersionAdmin):
    pass


@admin.register(ComponentModel)
class ComponentModelAdmin(reversion.VersionAdmin):
    pass


@admin.register(GenericComponent)
class GenericComponentAdmin(reversion.VersionAdmin):
    pass


@admin.register(Network)
class NetworkAdmin(reversion.VersionAdmin):
    pass


@admin.register(NetworkEnvironment)
class NetworkEnvironmentAdmin(reversion.VersionAdmin):
    pass


@admin.register(NetworkKind)
class NetworkKindAdmin(reversion.VersionAdmin):
    pass


@admin.register(NetworkTerminator)
class NetworkTerminatorAdmin(reversion.VersionAdmin):
    pass


@admin.register(DiscoveryQueue)
class DiscoveryQueueAdmin(reversion.VersionAdmin):
    pass


@admin.register(IPAddress)
class IPAddressAdmin(reversion.VersionAdmin):
    pass
