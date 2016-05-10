# -*- coding: utf-8 -*-
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphMPTTAdmin, RalphTabularInline, register
from ralph.admin.views.extra import RalphDetailView
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
from ralph.assets.models.components import (
    ComponentModel,
    Ethernet,
    GenericComponent
)
from ralph.assets.models.configuration import (
    ConfigurationClass,
    ConfigurationModule
)
from ralph.data_importer import resources
from ralph.lib.table import Table, TableWithUrl


@register(ConfigurationClass)
class ConfigurationClassAdmin(RalphAdmin):
    fields = ['class_name', 'module', 'path']
    readonly_fields = ['path']
    raw_id_fields = ['module']
    search_fields = [
        'path',
    ]
    list_display = ['class_name', 'module', 'path', 'objects_count']
    list_select_related = ['module']
    list_filter = ['class_name', 'module']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(objects_count=Count('baseobject'))
        return qs

    def objects_count(self, instance):
        return instance.objects_count
    objects_count.short_description = _('Objects count')
    objects_count.admin_order_field = 'objects_count'


@register(ConfigurationModule)
class ConfigurationModuleAdmin(RalphMPTTAdmin):
    list_display = ['name']
    search_fields = ['name']
    readonly_fields = [
        'show_children_modules', 'show_children_classes'
    ]
    raw_id_fields = ['parent']
    fieldsets = (
        (_('Basic info'), {
            'fields': [
                'name', 'parent', 'support_team'
            ]
        }),
        (_('Relations'), {
            'fields': [
                'show_children_modules', 'show_children_classes'
            ]
        })
    )

    def show_children_modules(self, module):
        if not module or not module.pk:
            return '&ndash;'
        return TableWithUrl(
            module.children_modules.all(),
            ['name'],
            url_field='name'
        ).render()
    show_children_modules.allow_tags = True
    show_children_modules.short_description = _('Children modules')

    def show_children_classes(self, module):
        if not module or not module.pk:
            return '&ndash;'
        return TableWithUrl(
            module.configuration_classes.all(),
            ['name'],
            url_field='name'
        ).render()
    show_children_classes.allow_tags = True
    show_children_classes.short_description = _('Children classes')


@register(ServiceEnvironment)
class ServiceEnvironmentAdmin(RalphAdmin):

    search_fields = ['service__name', 'environment__name']
    list_select_related = ['service', 'environment']
    raw_id_fields = ['service', 'environment']
    resource_class = resources.ServiceEnvironmentResource
    exclude = ('parent', 'service_env', 'content_type')


class ServiceEnvironmentInline(RalphTabularInline):
    model = ServiceEnvironment
    raw_id_fields = ['environment']
    fields = ('environment',)


class BaseObjectsList(Table):
    def url(self, item):
        return '<a href="{}">{}</a>'.format(
            item.get_absolute_url(),
            _('Go to object')
        )
    url.title = _('Link')

    def _str(self, item):
        return str(item)
    _str.title = _('object')


class ServiceBaseObjects(RalphDetailView):
    icon = 'bookmark'
    name = 'service_base_objects'
    label = _('Objects')
    url_name = 'service_base_objects'

    def get_service_base_objects_queryset(self):
        return BaseObject.polymorphic_objects.filter(
            service_env__service=self.object
        ).select_related('service_env__environment', 'content_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_objects_list'] = BaseObjectsList(
            self.get_service_base_objects_queryset(),
            [
                'id', ('content_type', _('type')),
                ('service_env__environment', _('environment')), '_str', 'url',
            ]
        )
        return context


@register(Service)
class ServiceAdmin(RalphAdmin):
    fields = (
        'name', 'uid', 'active', 'profit_center', 'cost_center',
        'technical_owners', 'business_owners', 'support_team',
    )
    inlines = [ServiceEnvironmentInline]
    search_fields = ['name', 'uid']
    raw_id_fields = [
        'profit_center', 'support_team', 'business_owners', 'technical_owners'
    ]
    resource_class = resources.ServiceResource
    change_views = [ServiceBaseObjects]


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
class AssetModelAdmin(RalphAdmin):

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
    search_fields = ['name']


@register(GenericComponent)
class GenericComponentAdmin(RalphAdmin):
    search_fields = ['name']


@register(Ethernet)
class EthernetAdmin(RalphAdmin):
    search_fields = ['label', 'mac']


@register(Asset)
class AssetAdmin(RalphAdmin):
    raw_id_fields = ['parent', 'service_env', 'model']
    search_fields = ['hostname', 'sn', 'barcode']


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
