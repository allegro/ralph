# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from mptt.utils import drilldown_tree_for_node

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.filters import (
    LiquidatedStatusFilter,
    TagsListFilter,
    TextListFilter
)
from ralph.admin.mixins import (
    BulkEditChangeListMixin,
    RalphAdminFormMixin,
    RalphMPTTAdmin
)
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models.components import GenericComponent as AssetComponent
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_center.forms.network import NetworkInlineFormset
from ralph.data_center.models.components import DiskShare, DiskShareMount
from ralph.data_center.models.networks import (
    DiscoveryQueue,
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind,
    NetworkTerminator
)
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
from ralph.lib.mixins.admin import MemorizeBeforeStateMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.supports.models import BaseObjectsSupport


class ParentChangeMixin(MemorizeBeforeStateMixin):
    add_message = None
    change_message = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_attr = self.model._parent_attr

    def get_add_message(self):
        return self.add_message

    def get_change_message(self):
        return self.change_message

    def response_add(self, request, obj, post_url_continue=None):
        parent = getattr(obj, self.parent_attr)
        if parent:
            message = None
            if obj:
                message = self.get_add_message().format(
                    parent.get_absolute_url(), parent
                )
                self.message_user(request, mark_safe(message))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        parent = getattr(obj, self.parent_attr)
        message = None
        old_parent = getattr(obj._before_state, self.parent_attr)
        if parent and old_parent != parent:
            # TODO: parent as None
            old_url = old_parent and old_parent.get_absolute_url() or '#'
            parent_url = parent and parent.get_absolute_url() or '#'
            message = self.get_change_message().format(
                old_url,
                old_parent,
                parent_url,
                parent
            )
        if message:
            self.message_user(request, mark_safe(message))
        return super().response_change(request, obj)


@register(Accessory)
class AccessoryAdmin(RalphAdmin):

    search_fields = ['name']


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):

    search_fields = ['name']


class NetworkInline(RalphTabularInline):
    formset = NetworkInlineFormset
    model = IPAddress


class NetworkView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'Network'
    url_name = 'network'

    inlines = [NetworkInline]


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
    show_transition_history = True
    resource_class = resources.DataCenterAssetResource
    list_display = [
        'status', 'barcode', 'model', 'sn', 'hostname', 'invoice_date',
        'invoice_no',
    ]
    multiadd_summary_fields = list_display + ['rack']
    one_of_mulitvalue_required = ['sn', 'barcode']
    bulk_edit_list = list_display + [
        'rack', 'orientation', 'position',
        'slot_no', 'price', 'provider', 'service_env'
    ]
    bulk_edit_no_fillable = ['barcode', 'sn']
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = [
        'status', 'barcode', 'sn', 'hostname', 'invoice_no', 'invoice_date',
        'order_no', 'model__name', 'service_env', 'depreciation_end_date',
        'force_depreciation', 'remarks', 'budget_info', 'rack__name',
        'rack__server_room', 'rack__server_room__data_center',
        'property_of', LiquidatedStatusFilter,
        ('management_ip', TextListFilter),
        'management_hostname', ('tags', TagsListFilter)
    ]
    date_hierarchy = 'created'
    list_select_related = ['model', 'model__manufacturer', 'model__category']
    raw_id_fields = ['model', 'rack', 'service_env', 'parent', 'budget_info']
    raw_id_override_parent = {'parent': DataCenterAsset}
    _invoice_report_name = 'invoice-data-center-asset'
    multiadd_clear_fields = [
        {'field': 'management_ip', 'value': None},
        {'field': 'management_hostname', 'value': None},
    ]

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


@register(NetworkEnvironment)
class NetworkEnvironmentAdmin(RalphAdmin):
    pass


@register(NetworkKind)
class NetworkKindAdmin(RalphAdmin):
    pass


@register(NetworkTerminator)
class NetworkTerminatorAdmin(RalphAdmin):
    pass


@register(DiscoveryQueue)
class DiscoveryQueueAdmin(RalphAdmin):
    pass


class AddNetworkForm(RalphAdminFormMixin, ModelForm):
    top_margin = forms.IntegerField()
    bottom_margin = forms.IntegerField()

    class Meta:
        model = Network
        exclude = ('parent',)


@register(Network)
class NetworkAdmin(RalphMPTTAdmin):
    change_form_template = 'admin/data_center/network/change_form.html'
    search_fields = ['address', 'remarks']
    list_display = ['name', 'address', 'kind', 'vlan']
    list_filter = ['kind', 'dhcp_broadcast']  # noqa add rack when multi widget will be available
    raw_id_fields = ['racks']
    resource_class = resources.NetworkResource
    # TODO: adapt form to handle change action
    add_form = AddNetworkForm

    add_message = _('Network added to <a href="{}" _target="blank">{}</a>')
    change_message = _('Network reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>')  # noqa

    def changeform_view(
        self, request, object_id=None, form_url='', extra_context=None
    ):
        if not extra_context:
            extra_context = {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['next_free_ip'] = obj.get_first_free_ip()
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        bottom_margin = form.cleaned_data.get('bottom_margin', None)
        top_margin = form.cleaned_data.get('top_margin', None)
        if all([bottom_margin, top_margin]):
            obj.reserve_margin_addresses(
                bottom_count=form.cleaned_data['bottom_margin'],
                top_count=form.cleaned_data['top_margin'],
            )
        obj.save()


@register(IPAddress)
class IPAddressAdmin(ParentChangeMixin, RalphAdmin):
    search_fields = ['address']
    list_filter = ['is_public', 'is_management']
    list_display = ['address', 'hostname', 'base_object_link', 'is_gateway']
    readonly_fields = ['get_network_path', 'is_public']
    list_select_related = ['base_object']
    raw_id_fields = ['base_object']
    resource_class = resources.IPAddressResource
    list_select_related = ['base_object__content_type']

    fieldsets = (
        (_('Basic info'), {
            'fields': [
                'address', 'get_network_path', 'base_object',
            ]
        }),
        (_('Additional info'), {
            'fields': [
                'hostname', 'is_management', 'is_public'
            ]
        }),
    )

    add_message = _('IP added to <a href="{}" _target="blank">{}</a>')
    change_message = _('IP reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>')  # noqa

    def get_network_path(self, obj):
        if not obj.network:
            return None
        nodes = obj.network.get_ancestors(include_self=True)
        nodes_link = []
        for node in nodes:
            nodes_link.append('<a href="{}" target="blank">{}</a>'.format(
                node.get_absolute_url(), node
            ))
        return ' > '.join(nodes_link)
    get_network_path.short_description = _('Network')
    get_network_path.allow_tags = True

    def base_object_link(self, obj):
        if not obj.base_object:
            return '&ndash;'
        ct = obj.base_object.content_type
        return '<a href="{}" target="_blank">{} ({})</a>'.format(
            reverse('admin:view_on_site', args=(ct.id, obj.base_object.id)),
            ct.model_class()._meta.verbose_name.capitalize(),
            obj.base_object.id,
        )
    base_object_link.short_description = _('Linked object')
    base_object_link.allow_tags = True
