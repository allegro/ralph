# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
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


@register(ServiceEnvironment)
class ServiceEnvironmentAdmin(RalphAdmin):
    pass


@register(Service)
class ServiceAdmin(RalphAdmin):
    pass


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):
    pass


@register(Environment)
class EnvironmentAdmin(RalphAdmin):
    pass


@register(AssetModel)
class AssetModelAdmin(RalphAdmin):
    pass


@register(Category)
class CategoryAdmin(RalphAdmin):
    pass


@register(ComponentModel)
class ComponentModelAdmin(RalphAdmin):
    pass


@register(GenericComponent)
class GenericComponentAdmin(RalphAdmin):
    pass
