from django.db.models import Prefetch
from django.template.defaultfilters import date, timesince_filter
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.dhcp.models import (
    DHCPServer,
    DNSServer,
    DNSServerGroup,
    DNSServerGroupOrder
)


@register(DHCPServer)
class DHCPServerAdmin(RalphAdmin):
    list_display = ['ip', 'last_synchronized_formatted', 'network_environment']
    list_select_related = ['network_environment']
    search_fields = ['ip']

    def last_synchronized_formatted(self, obj):
        return _('{} ({} ago)'.format(
            date(obj.last_synchronized),
            timesince_filter(obj.last_synchronized)
        ))
    last_synchronized_formatted.short_description = 'Last synchronized'


@register(DNSServer)
class DNSServerAdmin(RalphAdmin):
    pass


class DNSServerGroupOrderInline(RalphTabularInline):
    model = DNSServerGroupOrder
    extra = 5


@register(DNSServerGroup)
class DNSServerGroupAdmin(RalphAdmin):
    fields = ('name',)
    inlines = (DNSServerGroupOrderInline,)
    list_display = ('name', 'servers_formatted')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            Prefetch(
                'server_group_order__dns_server',
                queryset=DNSServer.objects.all().only('ip_address').order_by(
                    'server_group_order__order'
                )
            )
        )

    def servers_formatted(self, obj):
        return ', '.join([
            d.dns_server.ip_address for d in obj.server_group_order.all()
        ])
    servers_formatted.short_description = 'DNS Servers'
