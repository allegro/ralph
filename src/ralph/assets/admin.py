# -*- coding: utf-8 -*-
from import_export.admin import ImportExportModelAdmin

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
from ralph.data_importer import resources


@register(ServiceEnvironment)
class ServiceEnvironmentAdmin(RalphAdmin):

    list_select_related = ['service', 'environment']


@register(Service)
class ServiceAdmin(RalphAdmin):
    pass


@register(Manufacturer)
class ManufacturerAdmin(ImportExportModelAdmin, RalphAdmin):
    pass


@register(Environment)
class EnvironmentAdmin(RalphAdmin):
    pass


@register(AssetModel)
class AssetModelAdmin(ImportExportModelAdmin, RalphAdmin):

    resource_class = resources.AssetModelResource

    list_select_related = ['manufacturer']
    raw_id_fields = ['manufacturer']


@register(Category)
class CategoryAdmin(RalphAdmin):
    pass


@register(ComponentModel)
class ComponentModelAdmin(RalphAdmin):
    pass


@register(GenericComponent)
class GenericComponentAdmin(RalphAdmin):
    pass
