# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.assets.models.assets import (
    Asset,
    AssetModel,
    BaseObject,
    Category,
    Environment,
    Manufacturer,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.components import ComponentModel, GenericComponent
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin


@register(ServiceEnvironment)
class ServiceEnvironmentAdmin(RalphAdmin):

    search_fields = ['service__name', 'environment__name']
    list_select_related = ['service', 'environment']
    resource_class = resources.ServiceEnvironmentResource


class ServiceEnvironmentInline(RalphTabularInline):
    model = ServiceEnvironment
    raw_id_fields = ['environment']


@register(Service)
class ServiceAdmin(RalphAdmin):
    exclude = ['environments']
    inlines = [ServiceEnvironmentInline]
    search_fields = ['name']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):

    search_fields = ['name']


@register(Environment)
class EnvironmentAdmin(RalphAdmin):

    search_fields = ['name']


@register(AssetModel)
class AssetModelAdmin(PermissionAdminMixin, RalphAdmin):

    resource_class = resources.AssetModelResource
    list_select_related = ['manufacturer']
    raw_id_fields = ['manufacturer']
    search_fields = ['name', 'manufacturer__name']
    ordering = ['name']
    fields = (
        'name', 'manufacturer', 'category', 'type', 'has_parent',
        'cores_count', 'height_of_device', 'power_consumption',
        'visualization_layout_front', 'visualization_layout_back'
    )


@register(Category)
class CategoryAdmin(RalphAdmin):

    search_fields = ['name']
    resource_class = resources.CategoryResource


@register(ComponentModel)
class ComponentModelAdmin(RalphAdmin):
    pass


@register(GenericComponent)
class GenericComponentAdmin(RalphAdmin):
    pass


@register(Asset)
class AssetAdmin(RalphAdmin):
    raw_id_fields = ['parent', 'service_env', 'model']


@register(BaseObject)
class BaseObjectAdmin(RalphAdmin):
    raw_id_fields = ['parent', 'service_env']
