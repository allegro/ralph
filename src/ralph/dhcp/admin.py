from django.template.defaultfilters import date, timesince_filter
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.dhcp.models import DHCPServer, DNSServer


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
