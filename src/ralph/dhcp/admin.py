from django.db.models import Prefetch
from django.template.defaultfilters import date, timesince_filter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin, RalphTabularInline
from ralph.dhcp.models import (
    DHCPServer,
    DNSServer,
    DNSServerGroup,
    DNSServerGroupOrder
)
from ralph.lib.table.table import TableWithUrl


@register(DHCPServer)
class DHCPServerAdmin(RalphAdmin):
    list_display = ["ip", "last_synchronized_formatted", "network_environment"]
    list_select_related = ["network_environment"]
    search_fields = ["ip"]

    def last_synchronized_formatted(self, obj):
        return _(
            "{} ({} ago)".format(
                date(obj.last_synchronized), timesince_filter(obj.last_synchronized)
            )
        )

    last_synchronized_formatted.short_description = "Last synchronized"


@register(DNSServer)
class DNSServerAdmin(RalphAdmin):
    pass


class DNSServerGroupOrderInline(RalphTabularInline):
    model = DNSServerGroupOrder
    extra = 5


@register(DNSServerGroup)
class DNSServerGroupAdmin(RalphAdmin):
    inlines = (DNSServerGroupOrderInline,)
    list_display = ("name", "servers_formatted")
    readonly_fields = ["networks"]
    fieldsets = (
        (
            _(""),
            {
                "fields": (
                    "name",
                    "networks",
                )
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                Prefetch(
                    "server_group_order__dns_server",
                    queryset=DNSServer.objects.all()
                    .only("ip_address")
                    .order_by("server_group_order__order"),
                )
            )
        )

    def servers_formatted(self, obj):
        return ", ".join(
            [d.dns_server.ip_address for d in obj.server_group_order.all()]
        )

    servers_formatted.short_description = "DNS Servers"

    @mark_safe
    def networks(self, obj):
        networks = obj.networks.all()
        if networks:
            result = TableWithUrl(
                networks,
                ["name", "address", "network_environment"],
                url_field="name",
            ).render()
        else:
            result = "&ndash;"
        return result

    networks.short_description = _("in networks")
