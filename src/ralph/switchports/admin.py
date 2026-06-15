from ralph.admin.decorators import register
from . import connections
from .models import Port
from ..admin.mixins import RalphAdmin


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
