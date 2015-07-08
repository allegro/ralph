# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ImportExportModelAdmin

from ralph.admin import RalphAdmin, register
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
    NetworkView,
)
from ralph.lib.permissions.admin import PermissionAdminMixin


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):

    search_fields = ['name']


@register(DataCenterAsset)
class DataCenterAssetAdmin(
    PermissionAdminMixin,
    ImportExportModelAdmin,
    RalphAdmin,
):
    """Data Center Asset admin class."""

    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetSoftware,
        NetworkView,
        DataCenterAssetSecurityInfo,
        DataCenterAssetLicence,
    ]
    resource_class = resources.DataCenterAssetResource
    list_display = [
        'status', 'barcode', 'purchase_order', 'model',
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


@register(ServerRoom)
class ServerRoomAdmin(RalphAdmin):

    list_select_related = ['data_center']
    search_fields = ['name', 'data_center__name']


@register(Rack)
class RackAdmin(RalphAdmin):

    search_fields = ['name']

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
    pass


@register(DiskShare)
class DiskShareAdmin(RalphAdmin):
    pass


@register(DiskShareMount)
class DiskShareMountAdmin(RalphAdmin):
    pass


@register(Network)
class NetworkAdmin(RalphAdmin):
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


@register(IPAddress)
class IPAddressAdmin(RalphAdmin):

    search_fields = ['address', 'hostname']
    list_filter = ['is_public', 'is_management']
