import ipaddress

from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import ChoicesListFilter, TextListFilter

PRIVATE_NETWORK_CIDRS = [
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
]


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


class NetworkClassFilter(ChoicesListFilter):
    _choices_list = [
        ('private', _('Private')),
        ('public', _('Public')),
    ]

    def queryset(self, request, queryset):
        if not self.value():
            pass
        elif self.value().lower() == 'private':
            queryset = queryset.filter(address__in=PRIVATE_NETWORK_CIDRS)
        elif self.value().lower() == 'public':
            queryset = queryset.exclude(address__in=PRIVATE_NETWORK_CIDRS)
        return queryset
