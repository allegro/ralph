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
from ralph.data_center.views import (
    DataCenterAssetComponents,
    DataCenterAssetSecurityInfo,
    DataCenterAssetSoftware,
    NetworkView
)


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):
    pass


@register(DataCenterAsset)
class DataCenterAssetAdmin(ImportExportModelAdmin, RalphAdmin):
    """Data Center Asset admin class."""

    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetSoftware,
        NetworkView,
        DataCenterAssetSecurityInfo,
    ]
    resource_class = resources.DataCenterAssetResource
    list_display = [
        'status', 'barcode', 'purchase_order', 'model',
        'sn', 'hostname', 'invoice_date', 'invoice_no'
    ]
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = ['status']
    date_hierarchy = 'created'
    list_select_related = ['model']

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
    pass


@register(Rack)
class RackAdmin(RalphAdmin):
    pass


@register(RackAccessory)
class RackAccessoryAdmin(RalphAdmin):
    pass


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
    pass
