# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import (
    IPFilter,
    LiquidatedStatusFilter,
    RelatedAutocompleteFieldListFilter,
    TagsListFilter,
    TreeRelatedAutocompleteFilterWithDescendants
)
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models.components import Ethernet
from ralph.assets.views import ComponentsAdminView
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_center.forms import DataCenterAssetForm
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
from ralph.data_center.models.virtual import (
    BaseObjectCluster,
    Cluster,
    ClusterType,
    Database,
    VIP
)
from ralph.data_center.views.ui import DataCenterAssetSecurityInfo
from ralph.data_importer import resources
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.table import Table
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence
from ralph.networks.forms import SimpleNetworkForm
from ralph.networks.models.networks import Network
from ralph.networks.views import NetworkWithTerminatorsView
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.supports.models import BaseObjectsSupport

if settings.ENABLE_DNSAAS_INTEGRATION:
    from ralph.dns.views import DNSView


@register(Accessory)
class AccessoryAdmin(RalphAdmin):

    search_fields = ['name']


class ClusterNetworkInline(RalphTabularInline):
    form = SimpleNetworkForm
    model = Ethernet
    exclude = ['model']


@register(ClusterType)
class ClusterTypeAdmin(RalphAdmin):

    search_fields = ['name']


@register(Cluster)
class ClusterAdmin(CustomFieldValueAdminMixin, RalphAdmin):

    search_fields = ['name', 'hostname']
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'hostname', 'type', 'status', 'remarks', 'service_env',
                'configuration_path',
                'tags'
            )
        }),
    )
    raw_id_fields = ['service_env', 'configuration_path']
    readonly_fields = ['get_masters_summary']
    list_display = ['id', 'name', 'hostname', 'type']
    list_select_related = ['type']
    list_filter = [
        'name', 'type', 'service_env', 'configuration_path', 'status'
    ]

    class ClusterBaseObjectInline(RalphTabularInline):
        model = BaseObjectCluster
        fk_name = 'cluster'
        raw_id_fields = ('base_object',)
        extra = 1
        verbose_name = _('Base Object')

    inlines = [ClusterBaseObjectInline, ClusterNetworkInline]

    def get_fieldsets(self, request, obj=None):
        """
        Attach master info fieldset only if show_master_summary option checked
        for cluster type.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.pk and obj.type.show_master_summary:
            fieldsets += ((
                _('Master Info'), {
                    'fields': (
                        'get_masters_summary',
                    )
                }
            ),)
        return fieldsets

    def get_masters_summary(self, obj):
        masters = obj.masters
        if not masters:
            return '-'
        return Table(
            masters,
            getattr(masters[0], '_summary_fields', []),
            transpose=True,
        ).render()
    get_masters_summary.allow_tags = True
    get_masters_summary.short_description = _('Master info')


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):

    search_fields = ['name']


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


class DataCenterAssetNetworkView(NetworkWithTerminatorsView):
    pass


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


class DataCenterAssetComponents(ComponentsAdminView):
    pass


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
    CustomFieldValueAdminMixin,
    RalphAdmin,
):
    """Data Center Asset admin class."""

    actions = ['bulk_edit_action']
    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetNetworkView,
        DataCenterAssetSecurityInfo,
        DataCenterAssetLicence,
        DataCenterAssetSupport,
        DataCenterAssetOperation,
    ]
    form = DataCenterAssetForm
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views += [DNSView]
    show_transition_history = True
    resource_class = resources.DataCenterAssetResource
    list_display = [
        'hostname', 'status', 'barcode', 'model', 'sn', 'invoice_date',
        'invoice_no', 'show_location', 'service_env',
    ]
    multiadd_summary_fields = list_display + ['rack']
    one_of_mulitvalue_required = ['sn', 'barcode']
    bulk_edit_list = [
        'hostname', 'status', 'barcode', 'model', 'sn', 'invoice_date',
        'invoice_no', 'rack', 'orientation', 'position', 'slot_no', 'price',
        'provider', 'service_env', 'tags'
    ]
    bulk_edit_no_fillable = ['barcode', 'sn']
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = [
        'status', 'barcode', 'sn', 'hostname', 'invoice_no', 'invoice_date',
        'order_no', 'model__name',
        ('model__category', RelatedAutocompleteFieldListFilter), 'service_env',
        ('configuration_path__module', TreeRelatedAutocompleteFilterWithDescendants),  # noqa
        'depreciation_end_date', 'force_depreciation', 'remarks', 'budget_info',
        'rack', 'rack__server_room', 'rack__server_room__data_center',
        'position', 'property_of', LiquidatedStatusFilter, IPFilter,
        ('tags', TagsListFilter)
    ]
    date_hierarchy = 'created'
    list_select_related = [
        'model', 'model__manufacturer', 'model__category', 'rack',
        'rack__server_room', 'rack__server_room__data_center', 'service_env',
        'service_env__service', 'service_env__environment',
        'configuration_path__module',
    ]
    raw_id_fields = [
        'model', 'rack', 'service_env', 'parent', 'budget_info',
        'configuration_path',
    ]
    raw_id_override_parent = {'parent': DataCenterAsset}
    _invoice_report_name = 'invoice-data-center-asset'

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
                'service_env', 'configuration_path', 'production_year',
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

    def show_location(self, obj):
        return obj.location
    show_location.short_description = _('Location')
    show_location.allow_tags = True


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
