from ralph.admin.decorators import register
from .models import Port
from ..admin.mixins import RalphAdmin


@register(Port)
class PortAdmin(RalphAdmin):
    list_display = ("label", "data_center_asset")
    list_filter = ("data_center_asset",)
    raw_id_fields = ("data_center_asset",)
