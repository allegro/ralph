from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ralph.admin.decorators import register
from . import connections
from .models import (
    Port,
    RackSwitchConfigurationOverride,
    SwitchportRefreshJob,
)
from .models.validation import DiffEntry, DiffStamp, SwitchportDiffStatus, MISMATCH_STATUSES
from ..admin.filters import ChoicesListFilter
from ..admin.helpers import generate_html_link
from ..admin.mixins import RalphAdmin
from ..data_center.models import DataCenterAsset


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
            self.message_user(request, "Please select exactly 2 ports to connect.", level="error")
            return
        try:
            connections.connect(*queryset[:])
        except:  # noqa
            self.message_user(request, "Failed to connect ports", level="error")


class SwitchportDiffStatusFilter(ChoicesListFilter):
    """Filter diff entries by status. Mismatched only by default"""

    title = "status"
    parameter_name = "status"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._choices_list = [
            ("mismatch", _("Mismatched")),
            ("all", _("All")),
            *[(status.value, status.label) for status in SwitchportDiffStatus],
        ]

    def choices(self, cl):
        for lookup, title in self.choices_list:
            yield {
                "selected": smart_str(lookup) == self.value(),
                "value": lookup,
                "display": title,
                "parameter_name": self.field_path,
            }

    def queryset(self, request, queryset):
        value = self.value()

        if not value or value == "mismatch":
            return queryset.filter(status__in=MISMATCH_STATUSES)

        if value == "all":
            return queryset

        statuses = value.split(",")

        return queryset.filter(status__in=statuses)


class SwitchportDiffStampFilter(ChoicesListFilter):
    """Filter diff entries by stamp. Unstamped by default"""

    title = _("Processed")
    parameter_name = "stamp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # otherwise title would be set from verbose_name
        self.title = SwitchportDiffStampFilter.title
        self._choices_list = [("no", _("Pending")), ("yes", _("Acknowledged")), ("all", _("All"))]

    def choices(self, cl):
        for lookup, title in self.choices_list:
            yield {
                "selected": smart_str(lookup) == self.value(),
                "value": lookup,
                "display": title,
                "parameter_name": self.field_path,
            }

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(stamp__isnull=False)
        elif self.value() == "all":
            return queryset

        return queryset.filter(stamp__isnull=True)


@register(DiffEntry)
class SwitchportReportAdmin(RalphAdmin):
    list_display = [
        "id",
        "_switch",
        "_port",
        "status",
        "_ralph_asset",
        "_netmaker_asset",
        "ack_by",
    ]
    list_filter = (
        ("status", SwitchportDiffStatusFilter),
        ("stamp", SwitchportDiffStampFilter),
    )
    readonly_fields = ["switch", "label", "status", "ralph_asset", "netmaker_asset"]
    actions = ("stamp_entries", "unstamp_entries")
    redirect_to_detail_view_if_one_search_result = False
    ordering = (
        "-modified",
        "-created",
    )

    def ack_by(self, obj):
        return None if obj.stamp is None else obj.stamp.actor.username

    def has_delete_permission(self, request, obj=None):
        return False

    def stamp_entries(self, request, queryset):
        DiffStamp.objects.bulk_create(
            [DiffStamp(entry=entry, actor=request.user) for entry in queryset],
            ignore_conflicts=True,
        )

    stamp_entries.short_description = _("Acknowledge entries")

    def unstamp_entries(self, request, queryset):
        DiffStamp.objects.filter(entry__in=queryset).delete()

    unstamp_entries.short_description = _("Unacknowledge entries")

    @mark_safe
    def _switch(self, obj):
        url = reverse("admin:data_center_datacenterasset_ports", args=(obj.switch.id,))
        return generate_html_link(url, str(obj.switch))

    _switch.short_description = _("Switch")

    def _port(self, obj):
        return obj.label

    _port.short_description = _("Port")

    def _link_to_grid(self, asset: DataCenterAsset):
        if asset and asset.rack:
            grid_url = reverse("admin:data_center_rack_switchport-grid", args=(asset.rack.id,))
            if barcode := getattr(asset, "barcode", None):
                return generate_html_link(grid_url + f"?highlight={barcode}", str(asset))
            return generate_html_link(grid_url, str(asset))
        return "&dash;"

    @mark_safe
    def _ralph_asset(self, obj):
        return self._link_to_grid(obj.ralph_asset)

    _ralph_asset.short_description = _("Ralph Asset")

    @mark_safe
    def _netmaker_asset(self, obj):
        asset = obj.netmaker_asset
        return self._link_to_grid(obj.netmaker_asset)

    _netmaker_asset.short_description = _("Netmaker Asset")
