# -*- coding: utf-8 -*-
from django.contrib.admin import TabularInline
from django.utils.translation import ugettext_lazy as _

from ralph.admin import (
    RalphAdmin,
    register,
)
from ralph.admin.views import RalphDetailViewAdmin
from ralph.data_importer import resources
from ralph.data_center.models.virtual import (
    CloudProject,
    Database,
    VIP,
    VirtualServer
)
from ralph.data_center.models.components import (
    DiskShare,
    DiskShareMount
)
from ralph.data_center.models.physical import (
    Connection,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom,
)
from ralph.data_center.models.networks import (
    DiscoveryQueue,
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind,
    NetworkTerminator,
)
from ralph.data_center.views.ui import (
    DataCenterAssetComponents,
    DataCenterAssetLicence,
    DataCenterAssetSecurityInfo,
    DataCenterAssetSoftware,
)
from ralph.lib.permissions.admin import PermissionAdminMixin


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):

    search_fields = ['name']


class NetworkInline(TabularInline):
    model = IPAddress


class NetworkView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'Network'
    url_name = 'network'

    inlines = [NetworkInline]


@register(DataCenterAsset)
class DataCenterAssetAdmin(PermissionAdminMixin, RalphAdmin):
    """Data Center Asset admin class."""

    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetSoftware,
        DataCenterAssetSecurityInfo,
        DataCenterAssetLicence,
        NetworkView,
    ]

    resource_class = resources.DataCenterAssetResource
    list_display = [
        'status', 'barcode', 'purchase_order', 'model__name',
        'sn', 'hostname', 'invoice_date', 'invoice_no'
    ]
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = ['status']
    date_hierarchy = 'created'
    list_select_related = ['model', 'model__manufacturer']
    raw_id_fields = ['model', 'rack', 'service_env']

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'model', 'purchase_order', 'niw', 'barcode', 'sn',
                'status', 'task_url',
                'loan_end_date', 'hostname', 'service_env',
                'production_year', 'production_use_date',
                'required_support', 'remarks'
            )
        }),
        (_('Financial Info'), {
            'fields': (
                'order_no', 'invoice_date', 'invoice_no', 'price',
                'deprecation_rate', 'source', 'request_date', 'provider',
                'provider_order_date', 'delivery_date', 'deprecation_end_date',
                'force_deprecation'
            )
        }),
        (_('Additional Info'), {
            'fields': (
                'rack', 'slots', 'slot_no', 'configuration_path',
                'position', 'orientation'
            )
        }),
    )

    def model__name(self, obj):
        return obj.model.name
    model__name.admin_order_field = 'model__name'


@register(ServerRoom)
class ServerRoomAdmin(RalphAdmin):

    list_select_related = ['data_center']
    search_fields = ['name', 'data_center__name']
    resource_class = resources.ServerRoomResource


class RackAccessoryInline(TabularInline):
    model = RackAccessory


@register(Rack)
class RackAdmin(RalphAdmin):

    exclude = ['accessories']
    list_display = ['name', 'server_room']
    list_filter = ['server_room__data_center']
    list_select_related = ['server_room', 'server_room__data_center']
    search_fields = ['name']
    inlines = [RackAccessoryInline]
    resource_class = resources.RackResource

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
    resource_class = resources.RackAccessoryResource


@register(Database)
class DatabaseAdmin(RalphAdmin):
    pass


@register(VIP)
class VIPAdmin(RalphAdmin):
    pass


@register(VirtualServer)
class VirtualServerAdmin(RalphAdmin):
    pass


@register(CloudProject)
class CloudProjectAdmin(RalphAdmin):
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


@register(Network)
class NetworkAdmin(RalphAdmin):

    resource_class = resources.NetworkResource


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


@register(IPAddress)
class IPAddressAdmin(RalphAdmin):

    search_fields = ['address', 'hostname']
    list_filter = ['is_public', 'is_management']
    list_display = ['address', 'hostname', 'asset', 'is_public']
    list_select_related = ['asset']
    raw_id_fields = ['asset', 'network']
    resource_class = resources.IPAddressResource
