import ipaddress

from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import TextListFilter


class IPRangeFilter(TextListFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = _('IP range')

    def queryset(self, request, queryset):
        if self.value():
            try:
                network = ipaddress.ip_network(self.value())
            except ValueError:
                return queryset
            min_ip = int(network.network_address)
            max_ip = int(network.broadcast_address)

            queryset = queryset.filter(number__gte=min_ip, number__lte=max_ip)
        return queryset


class NetworkRangeFilter(TextListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.model_admin = model_admin
        super().__init__(
            field, request, params, model, model_admin, field_path
        )
        self.title = _('Network range')

    def queryset(self, request, queryset):
        if self.value():
            try:
                network = ipaddress.ip_network(self.value())
            except ValueError:
                return queryset

            min_ip = int(network.network_address)
            max_ip = int(network.broadcast_address)

            queryset = queryset.filter(min_ip__gte=min_ip, max_ip__lte=max_ip)
        return queryset
