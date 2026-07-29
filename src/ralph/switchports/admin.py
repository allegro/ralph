from ralph.admin.decorators import register
from . import connections
from .models import (
    Port,
    RackSwitchConfigurationOverride,
    SwitchportRefreshJob,
)
from ..admin.mixins import RalphAdmin


@register(RackSwitchConfigurationOverride)
class RackSwitchConfigurationOverrideAdmin(RalphAdmin):
    list_display = ("rack_switch_configuration", "data_center_asset", "switch")
    list_filter = ("rack_switch_configuration__label",)
    raw_id_fields = ("rack_switch_configuration", "data_center_asset", "switch")
    search_fields = (
        "data_center_asset__hostname",
        "data_center_asset__barcode",
        "switch__hostname",
        "switch__barcode",
    )


@register(SwitchportRefreshJob)
class SwitchportRefreshJobAdmin(RalphAdmin):
    list_display = ("rack_configuration", "status", "started_at", "finished_at")
    list_filter = ("status",)
    search_fields = ("rack_configuration__rack__name",)
    readonly_fields = (
        "rack_configuration",
        "status",
        "started_at",
        "finished_at",
        "summary",
        "error",
        "created",
        "modified",
    )

    def has_add_permission(self, request):
        return False


@register(Port)
class PortAdmin(RalphAdmin):
    list_display = ("label", "data_center_asset", "connected_to")
    list_filter = ("data_center_asset",)
    raw_id_fields = ("data_center_asset",)
    search_fields = (
        "label",
        "data_center_asset__hostname",
        "data_center_asset__barcode",
    )
    actions = ("connect",)

    def connected_to(self, obj):
        connection = getattr(obj, "connectionmember", None)
        if connection:
            other_ports = connection.connection.members.exclude(port=obj)
            return ", ".join(str(p.port) for p in other_ports)
        return "-"

    def connect(self, request, queryset):
        if queryset.count() != 2:
            self.message_user(
                request, "Please select exactly 2 ports to connect.", level="error"
            )
            return
        try:
            connections.connect(*queryset[:])
        except:  # noqa
            self.message_user(request, "Failed to connect ports", level="error")
