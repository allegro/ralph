# -*- coding: utf-8 -*-
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphMPTTAdmin, RalphTabularInline, register
from ralph.assets.models.assets import (
    Asset,
    AssetHolder,
    AssetModel,
    BaseObject,
    BudgetInfo,
    BusinessSegment,
    Category,
    Environment,
    Manufacturer,
    ProfitCenter,
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
    raw_id_fields = ['service', 'environment']
    resource_class = resources.ServiceEnvironmentResource
    exclude = ('parent', 'service_env')


class ServiceEnvironmentInline(RalphTabularInline):
    model = ServiceEnvironment
    raw_id_fields = ['environment']


@register(Service)
class ServiceAdmin(RalphAdmin):
    exclude = ['environments']
    inlines = [ServiceEnvironmentInline]
    filter_horizontal = ['business_owners', 'technical_owners']
    search_fields = ['name', 'uid']


@register(Manufacturer)
class ManufacturerAdmin(RalphAdmin):

    search_fields = ['name']


@register(BudgetInfo)
class BudgetInfoAdmin(RalphAdmin):

    search_fields = ['name']


@register(Environment)
class EnvironmentAdmin(RalphAdmin):

    search_fields = ['name']


@register(BusinessSegment)
class BusinessSegmentAdmin(RalphAdmin):

    search_fields = ['name']


@register(ProfitCenter)
class ProfitCenterAdmin(RalphAdmin):

    search_fields = ['name']


@register(AssetModel)
class AssetModelAdmin(PermissionAdminMixin, RalphAdmin):

    resource_class = resources.AssetModelResource
    list_select_related = ['manufacturer', 'category']
    list_display = ['name', 'type', 'manufacturer', 'category', 'assets_count']
    raw_id_fields = ['manufacturer']
    search_fields = ['name', 'manufacturer__name']
    list_filter = ['type', 'manufacturer', 'category']
    ordering = ['name']
    fields = (
        'name', 'manufacturer', 'category', 'type', 'has_parent',
        'cores_count', 'height_of_device', 'power_consumption',
        'visualization_layout_front', 'visualization_layout_back'
    )

    def get_queryset(self, request):
        return AssetModel.objects.annotate(assets_count=Count('assets'))

    def assets_count(self, instance):
        return instance.assets_count
    assets_count.short_description = _('Assets count')
    assets_count.admin_order_field = 'assets_count'


@register(Category)
class CategoryAdmin(RalphMPTTAdmin):

    search_fields = ['name']
    list_display = ['name', 'code']
    resource_class = resources.CategoryResource

    def get_actions(self, request):
        return []


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
    list_display = ['repr']
    raw_id_fields = ['parent', 'service_env']
    exclude = ('content_type',)
    list_select_related = ['content_type']

    def repr(self, obj):
        return '{}: {}'.format(obj.content_type, obj)


@register(AssetHolder)
class AssetHolderAdmin(RalphAdmin):

    search_fields = ['name']
