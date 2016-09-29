# -*- coding: utf-8 -*-
import operator
from functools import reduce

from django.conf import settings
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, Q
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import (
    BaseObjectHostnameFilter,
    ChoicesListFilter,
    IPFilter,
    LiquidatedStatusFilter,
    MacAddressFilter,
    RelatedAutocompleteFieldListFilter,
    TagsListFilter,
    TreeRelatedAutocompleteFilterWithDescendants
)
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models.base import BaseObject
from ralph.assets.models.components import Ethernet
from ralph.assets.views import ComponentsAdminView
from ralph.attachments.admin import AttachmentsMixin
from ralph.cross_validator.views import ShowDiffMessageMixin
from ralph.data_center.forms import DataCenterAssetForm
from ralph.data_center.models.components import DiskShare, DiskShareMount
from ralph.data_center.models.hosts import DCHost
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
from ralph.data_importer import resources
from ralph.deployment.mixins import ActiveDeploymentMessageMixin
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.table import Table
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence
from ralph.networks.forms import SimpleNetworkWithManagementIPForm
from ralph.networks.models.networks import Network
from ralph.networks.views import NetworkWithTerminatorsView
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.security.views import SecurityInfo
from ralph.supports.models import BaseObjectsSupport


class DCHostTypeListFilter(ChoicesListFilter):
    def __init__(self, *args, **kwargs):
        from ralph.data_center.models import Cluster, DataCenterAsset
        from ralph.virtual.models import CloudHost, VirtualServer
        models = [Cluster, DataCenterAsset, CloudHost, VirtualServer]
        self.choices_list = [
            (
                ContentType.objects.get_for_model(model).pk,
                model._meta.verbose_name
            )
            for model in models
        ]
        super().__init__(*args, **kwargs)


class DCHostHostnameFilter(SimpleListFilter):
    title = _('Hostname')
    parameter_name = 'hostname'
    template = 'admin/filters/text_filter.html'

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        fields = [
            'asset__hostname',
            'cloudhost__hostname',
            'cluster__hostname',
            'virtualserver__hostname',
            'ethernet_set__ipaddress__hostname'
        ]
        # TODO: simple if hostname would be in one model
        queries = [
            Q(**{'{}__icontains'.format(field): self.value()})
            for field in fields
        ]
        return queryset.filter(reduce(operator.or_, queries)).distinct()

    def lookups(self, request, model_admin):
        return (
            (1, _('Hostname')),
        )

    def choices(self, cl):
        yield {
            'selected': self.value(),
            'parameter_name': self.parameter_name,
        }


if settings.ENABLE_DNSAAS_INTEGRATION:
    from ralph.dns.views import DNSView

    class ClusterDNSView(DNSView):
        pass


@register(Accessory)
class AccessoryAdmin(RalphAdmin):

    search_fields = ['name']


class ClusterNetworkInline(RalphTabularInline):
    form = SimpleNetworkWithManagementIPForm
    model = Ethernet
    exclude = ['model']


@register(ClusterType)
class ClusterTypeAdmin(RalphAdmin):

    search_fields = ['name']


@register(Cluster)
class ClusterAdmin(CustomFieldValueAdminMixin, RalphAdmin):

    search_fields = ['name', 'hostname', 'ethernet_set__ipaddress__hostname']
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
        'name', BaseObjectHostnameFilter, 'type', 'service_env',
        'configuration_path', 'status'
    ]
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views = [ClusterDNSView]

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


class DataCenterAssetSecurityInfo(SecurityInfo):
    url_name = 'datacenter_asset_security_info'


@register(DataCenterAsset)
class DataCenterAssetAdmin(
    ActiveDeploymentMessageMixin,
    MulitiAddAdminMixin,
    TransitionAdminMixin,
    BulkEditChangeListMixin,
    AttachmentsMixin,
    AssetInvoiceReportMixin,
    CustomFieldValueAdminMixin,
    ShowDiffMessageMixin,
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
        'hostname',
        'status',
        'barcode',
        'model',
        'sn',
        'invoice_date',
        'invoice_no',
        'show_location',
        'service_env',
        'configuration_path',
    ]
    multiadd_summary_fields = list_display + ['rack']
    one_of_mulitvalue_required = ['sn', 'barcode']
    bulk_edit_list = [
        'hostname', 'status', 'barcode', 'model', 'sn', 'invoice_date',
        'invoice_no', 'rack', 'orientation', 'position', 'slot_no', 'price',
        'provider', 'service_env', 'configuration_path', 'tags'
    ]
    bulk_edit_no_fillable = ['barcode', 'sn']
    search_fields = [
        'barcode', 'sn', 'hostname', 'invoice_no', 'order_no',
        'ethernet_set__ipaddress__address', 'ethernet_set__ipaddress__hostname'
    ]
    list_filter = [
        'status', 'barcode', 'sn', 'hostname', 'invoice_no', 'invoice_date',
        'order_no', 'model__name',
        ('model__category', RelatedAutocompleteFieldListFilter), 'service_env',
        'configuration_path',
        ('configuration_path__module', TreeRelatedAutocompleteFilterWithDescendants),  # noqa
        MacAddressFilter,
        'depreciation_end_date', 'force_depreciation', 'remarks',
        'budget_info', 'rack', 'rack__server_room',
        'rack__server_room__data_center', 'position', 'property_of',
        LiquidatedStatusFilter, IPFilter, TagsListFilter
    ]
    date_hierarchy = 'created'
    list_select_related = [
        'model',
        'model__manufacturer',
        'model__category',
        'rack',
        'rack__server_room',
        'rack__server_room__data_center',
        'service_env',
        'service_env__service',
        'service_env__environment',
        'configuration_path',
    ]
    raw_id_fields = [
        'model', 'rack', 'service_env', 'parent', 'budget_info',
        'configuration_path',
    ]
    raw_id_override_parent = {'parent': DataCenterAsset}
    _invoice_report_name = 'invoice-data-center-asset'
    readonly_fields = ['get_created_date']

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'hostname', 'model', 'status', 'barcode', 'sn', 'niw',
                'required_support', 'remarks', 'tags', 'property_of',
                'firmware_version', 'bios_version',
            )
        }),
        (_('Location Info'), {
            'fields': (
                'rack', 'position', 'orientation', 'slot_no', 'parent',
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
                'budget_info', 'get_created_date',
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

    def get_created_date(self, obj):
        """
        Return created date for asset (since created is blacklisted by
        permissions, it cannot be displayed directly, because only superuser
        will see it)
        """
        return obj.created or '-'
    get_created_date.short_description = _('Created at')


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


class DCHostChangeList(ChangeList):
    def url_for_result(self, result):
        return result.get_absolute_url()


@register(DCHost)
class DCHostAdmin(RalphAdmin):
    search_fields = [
        'remarks',
        'asset__hostname',
        'cloudhost__hostname',
        'cluster__hostname',
        'virtualserver__hostname',
        'ethernet_set__ipaddress__address',
        'ethernet_set__ipaddress__hostname'
    ]
    list_display = [
        'get_hostname',
        'content_type',
        'service_env',
        'configuration_path',
        'show_location',
        'remarks',
    ]
    # TODO: sn
    # TODO: hostname, DC
    list_filter = [
        DCHostHostnameFilter,
        'service_env',
        'configuration_path',
        ('content_type', DCHostTypeListFilter),
        MacAddressFilter,
        IPFilter,
    ]
    list_select_related = [
        'content_type',
        'configuration_path',
        'service_env',
        'service_env__environment',
        'service_env__service',
    ]

    def has_add_permission(self, request):
        return False

    def get_changelist(self, request, **kwargs):
        return DCHostChangeList

    def get_actions(self, request):
        return None

    def get_hostname(self, obj):
        return obj.hostname
    get_hostname.short_description = _('Hostname')
    # TODO: simple if hostname would be in one model
    # get_hostname.admin_order_field = 'asset__hostname'

    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        # fixed issue with proxy model
        self.opts = BaseObject._meta

    def _initialize_search_form(self, extra_context, fields_from_model=True):
        return super()._initialize_search_form(extra_context)

    def show_location(self, obj):
        if hasattr(obj, 'get_location'):
            return ' / '.join(obj.get_location())
        return ''
    show_location.short_description = _('Location')
    show_location.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # location
        polymorphic_select_related = dict(
            DataCenterAsset=[
                'rack__server_room__data_center', 'model'
            ],
            VirtualServer=[
                'parent__asset__datacenterasset__rack__server_room__data_center',  # noqa
            ],
            CloudHost=[
                'hypervisor__rack__server_room__data_center'
            ]
        )
        qs = qs.polymorphic_select_related(**polymorphic_select_related)
        qs = qs.polymorphic_prefetch_related(Cluster=[
            Prefetch(
                'baseobjectcluster_set__base_object',
                queryset=BaseObject.polymorphic_objects.polymorphic_select_related(  # noqa
                    **polymorphic_select_related
                )
            )
        ])
        return qs
