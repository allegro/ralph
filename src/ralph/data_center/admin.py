# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import IPFilter, LiquidatedStatusFilter, TagsListFilter
from ralph.admin.helpers import generate_html_link
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models.components import GenericComponent as AssetComponent
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_center.models.components import DiskShare, DiskShareMount
from ralph.data_center.models.physical import (
    Accessory,
    Connection,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
)
from ralph.data_center.models.virtual import Database, VIP
from ralph.data_center.views.ui import DataCenterAssetSecurityInfo
from ralph.data_importer import resources
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence
from ralph.networks.forms import NetworkInlineFormset
from ralph.networks.models.networks import IPAddress, Network
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.supports.models import BaseObjectsSupport

if settings.ENABLE_DNSAAS_INTEGRATION:
    from ralph.dns.views import DNSView


@register(Accessory)
class AccessoryAdmin(RalphAdmin):

    search_fields = ['name']


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):

    search_fields = ['name']


class NetworkInline(RalphTabularInline):
    formset = NetworkInlineFormset
    model = IPAddress
    exclude = ['status']


class NetworkTerminatorReadOnlyInline(RalphTabularM2MInline):
    model = Network
    extra = 0
    show_change_link = True
    verbose_name_plural = _('Terminators of')
    fields = [
        'name', 'address',
    ]

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def has_add_permission(self, request):
        return False


class NetworkView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'Network'
    url_name = 'network'

    inlines = [NetworkInline, NetworkTerminatorReadOnlyInline]


class DataCenterAssetSupport(RalphDetailViewAdmin):
    icon = 'bookmark'
    name = 'dc_asset_support'
    label = _('Supports')
    url_name = 'data_center_asset_support'

    class DataCenterAssetSupportInline(RalphTabularInline):
        model = BaseObjectsSupport
        raw_id_fields = ('support',)
        extra = 1
        verbose_name = _('Support')
        ordering = ['-support__date_to']

    inlines = [DataCenterAssetSupportInline]


class DataCenterAssetLicence(RalphDetailViewAdmin):
    icon = 'key'
    name = 'dc_asset_licences'
    label = _('Licences')
    url_name = 'data_center_asset_licences'

    class DataCenterAssetLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ('licence',)
        extra = 1

    inlines = [DataCenterAssetLicenceInline]


class DataCenterAssetComponents(RalphDetailViewAdmin):
    icon = 'folder'
    name = 'dc_components'
    label = _('Components')
    url_name = 'datacenter_asset_components'

    class DataCenterComponentsInline(RalphTabularInline):
        model = AssetComponent
        raw_id_fields = ('model',)
        extra = 1

    inlines = [DataCenterComponentsInline]


class DataCenterAssetOperation(OperationViewReadOnlyForExisiting):
    name = 'dc_asset_operations'
    url_name = 'data_center_asset_operations'
    inlines = OperationViewReadOnlyForExisiting.admin_class.inlines


@register(DataCenterAsset)
class DataCenterAssetAdmin(
    MulitiAddAdminMixin,
    TransitionAdminMixin,
    BulkEditChangeListMixin,
    AttachmentsMixin,
    AssetInvoiceReportMixin,
    RalphAdmin,
):
    """Data Center Asset admin class."""

    actions = ['bulk_edit_action']
    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetSecurityInfo,
        DataCenterAssetLicence,
        DataCenterAssetSupport,
        DataCenterAssetOperation,
        NetworkView,
    ]
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views += [DNSView]
    show_transition_history = True
    resource_class = resources.DataCenterAssetResource
    list_display = [
        'status', 'barcode', 'model', 'sn', 'hostname', 'invoice_date',
        'localization',
    ]
    multiadd_summary_fields = list_display + ['rack']
    one_of_mulitvalue_required = ['sn', 'barcode']
    bulk_edit_list = [
        'status', 'barcode', 'model', 'sn', 'hostname', 'invoice_date',
        'rack', 'orientation', 'position', 'slot_no', 'price', 'provider',
        'service_env'
    ]
    bulk_edit_no_fillable = ['barcode', 'sn']
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = [
        'status', 'barcode', 'sn', 'hostname', 'invoice_no', 'invoice_date',
        'order_no', 'model__name', 'service_env', 'depreciation_end_date',
        'force_depreciation', 'remarks', 'budget_info', 'rack',
        'rack__server_room', 'rack__server_room__data_center', 'position',
        'property_of', LiquidatedStatusFilter, IPFilter,
        ('tags', TagsListFilter)
    ]
    date_hierarchy = 'created'
    list_select_related = [
        'model', 'model__manufacturer', 'model__category', 'rack',
        'rack__server_room', 'rack__server_room__data_center'
    ]
    raw_id_fields = ['model', 'rack', 'service_env', 'parent', 'budget_info']
    raw_id_override_parent = {'parent': DataCenterAsset}
    _invoice_report_name = 'invoice-data-center-asset'
    readonly_fields = ('management_ip', 'management_hostname')

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'hostname', 'model', 'status', 'barcode', 'sn', 'niw',
                'required_support', 'remarks', 'parent', 'tags', 'property_of'
            )
        }),
        (_('Location Info'), {
            'fields': (
                'rack', 'position', 'orientation', 'slot_no',
                'management_ip', 'management_hostname',
            )
        }),
        (_('Usage info'), {
            'fields': (
                'service_env', 'production_year',
                'production_use_date',
            )
        }),
        (_('Financial & Order Info'), {
            'fields': (
                'order_no', 'invoice_date', 'invoice_no', 'task_url', 'price',
                'depreciation_rate', 'depreciation_end_date',
                'force_depreciation', 'source', 'provider', 'delivery_date',
                'budget_info',
            )
        }),
    )

    def get_multiadd_fields(self, obj=None):
        multiadd_fields = [
            {'field': 'sn', 'allow_duplicates': False},
            {'field': 'barcode', 'allow_duplicates': False},
        ]
        return getattr(
            settings, 'MULTIADD_DATA_CENTER_ASSET_FIELDS', None
        ) or multiadd_fields

    def localization(self, obj):
        """
        Additional column 'localization' display filter by:
        data center, server_room, rack, position (if is blade)
        """
        base_url = reverse('admin:data_center_datacenterasset_changelist')
        position = obj.position
        if obj.is_blade:
            position = generate_html_link(
                base_url,
                {
                    'rack': obj.rack_id,
                    'position__start': obj.position,
                    'position__end': obj.position
                },
                position,
            )

        result = [
            generate_html_link(
                base_url,
                {
                    'rack__server_room__data_center':
                        obj.rack.server_room.data_center_id
                },
                obj.rack.server_room.data_center.name
            ),
            generate_html_link(
                base_url,
                {'rack__server_room': obj.rack.server_room_id},
                obj.rack.server_room.name
            ),
            generate_html_link(
                base_url,
                {'rack': obj.rack_id},
                obj.rack.name
            )
        ] if obj.rack else []

        if obj.position:
            result.append(str(position))
        if obj.slot_no:
            result.append(str(obj.slot_no))

        return '&nbsp;/&nbsp;'.join(result) if obj.rack else '&mdash;'

    localization.short_description = _('Localization')
    localization.allow_tags = True


@register(ServerRoom)
class ServerRoomAdmin(RalphAdmin):

    list_select_related = ['data_center']
    search_fields = ['name', 'data_center__name']
    resource_class = resources.ServerRoomResource
    list_display = ['name', 'data_center']


class RackAccessoryInline(RalphTabularInline):
    model = RackAccessory


@register(Rack)
class RackAdmin(RalphAdmin):

    exclude = ['accessories']
    list_display = ['name', 'server_room_name', 'data_center_name']
    list_filter = ['server_room__data_center']  # TODO use fk field in filter
    list_select_related = ['server_room', 'server_room__data_center']
    search_fields = ['name']
    inlines = [RackAccessoryInline]
    resource_class = resources.RackResource

    def server_room_name(self, obj):
        return obj.server_room.name if obj.server_room else ''
    server_room_name.short_description = _('Server room')
    server_room_name.admin_order_field = 'server_room__name'

    def data_center_name(self, obj):
        return obj.server_room.data_center.name if obj.server_room else ''
    data_center_name.short_description = _('Data Center')
    data_center_name.admin_order_field = 'server_room__data_center__name'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "server_room":
            kwargs["queryset"] = ServerRoom.objects.select_related(
                'data_center',
            )
        return super(RackAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@register(RackAccessory)
class RackAccessoryAdmin(RalphAdmin):

    list_select_related = ['rack', 'accessory']
    search_fields = ['accessory__name', 'rack__name']
    raw_id_fields = ['rack']
    list_display = ['__str__', 'position']
    resource_class = resources.RackAccessoryResource


@register(Database)
class DatabaseAdmin(RalphAdmin):
    pass


@register(VIP)
class VIPAdmin(RalphAdmin):
    pass


@register(Connection)
class ConnectionAdmin(RalphAdmin):

    resource_class = resources.ConnectionResource


@register(DiskShare)
class DiskShareAdmin(RalphAdmin):
    pass


@register(DiskShareMount)
class DiskShareMountAdmin(RalphAdmin):
    pass
