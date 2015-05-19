# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register

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


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):
    pass


@register(DataCenterAsset)
class DataCenterAssetAdmin(RalphAdmin):
    list_display = [
        'formatted_hostname', 'slots', 'rack', 'configuration_path'
    ]
    list_editable = ['slots', 'rack', 'configuration_path']
    raw_id_fields = 'rack',

    def get_list_display(self, obj):
        return ['slots']

    def formatted_hostname(self, obj):
        return '<strong style="color:red">{}</strong>'.format(
            obj.hostname or 'empty'
        )
    formatted_hostname.allow_tags = True


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
