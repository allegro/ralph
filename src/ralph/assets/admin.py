# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.components import (
    ComponentModel,
    GenericComponent
)


@admin.register(ServiceEnvironment)
class ServiceEnvironmentAdmin(reversion.VersionAdmin):
    pass


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
