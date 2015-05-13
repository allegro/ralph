# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin

from ralph.datacenter.models import (
    CloudProject,
    Connection,
    Database,
    DataCenter,
    DataCenterAsset,
    DiskShare,
    DiskShareMount,
    ServerRoom,
    Rack,
    RackAccessory,
    VIP,
    VirtualServer
)


@admin.register(DataCenter)
class DataCenterAdmin(reversion.VersionAdmin):
    pass


@admin.register(DataCenterAsset)
class DataCenterAssetAdmin(reversion.VersionAdmin):
    pass


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