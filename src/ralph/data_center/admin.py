# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

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
    list_display = ['formatted_hostname', 'slots', 'rack', 'configuration_path']
    list_editable = ['slots', 'rack', 'configuration_path']
    raw_id_fields = 'rack',

    def get_list_display(self, obj):
        return ['slots']

    def formatted_hostname(self, obj):
        return '<strong style="color:red">{}</strong>'.format(obj.hostname or 'puste')
    formatted_hostname.allow_tags = True


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
