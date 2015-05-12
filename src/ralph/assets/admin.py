# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.assets.models import (
    AssetModel,
    BOAsset,
    Category,
    CloudProject,
    Database,
    DCAsset,
    Environment,
    Manufacturer,
    Service,
    VIP,
    VirtualServer,
    Warehouse,
)


@admin.register(Service)
class ServiceAdmin(reversion.VersionAdmin):
    pass


@admin.register(Warehouse)
class WarehouseAdmin(reversion.VersionAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerAdmin(reversion.VersionAdmin):
    pass


@admin.register(Database)
class DatabaseAdmin(reversion.VersionAdmin):
    pass


@admin.register(VIP)
class VIPAdmin(reversion.VersionAdmin):
    pass


@admin.register(VirtualServer)
class VirtualServerAdmin(reversion.VersionAdmin):
    pass


@admin.register(CloudProject)
class CloudProjectAdmin(reversion.VersionAdmin):
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


@admin.register(DCAsset)
class DCAssetAdmin(reversion.VersionAdmin):
    base_model = DCAsset


@admin.register(BOAsset)
class BOAssetAdmin(reversion.VersionAdmin):
    base_model = BOAsset
