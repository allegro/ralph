# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

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
    ServerRoom,
    RackAccessory,
    Rack
)


@admin.register(DataCenter)
class DataCenterAdmin(reversion.VersionAdmin):
    pass


@admin.register(DataCenterAsset)
class DataCenterAssetAdmin(reversion.VersionAdmin):
    """Data Center Asset admin class."""

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


@admin.register(ServerRoom)
class ServerRoomAdmin(reversion.VersionAdmin):
    pass


@admin.register(Rack)
class RackAdmin(reversion.VersionAdmin):
    pass


@admin.register(RackAccessory)
class RackAccessoryAdmin(reversion.VersionAdmin):
    pass


@admin.register(Database)
class DatabaseAdmin(reversion.VersionAdmin):
    pass


@admin.register(VIP)
class VIPAdmin(reversion.VersionAdmin):
    pass


@admin.register(VirtualServer)
class VirtualServerAdmin(reversion.VersionAdmin):
    pass


@admin.register(CloudProject)
class CloudProjectAdmin(reversion.VersionAdmin):
    pass


@admin.register(Connection)
class ConnectionAdmin(reversion.VersionAdmin):
    pass


@admin.register(DiskShare)
class DiskShareAdmin(reversion.VersionAdmin):
    pass


@admin.register(DiskShareMount)
class DiskShareMountAdmin(reversion.VersionAdmin):
    pass
