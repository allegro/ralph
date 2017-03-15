import ipaddress
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import (
    ChoicesListFilter,
    SEARCH_OR_SEPARATORS,
    TextListFilter
)

PRIVATE_NETWORK_CIDRS = [
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
]


def get_private_network_filter():
    filter_ = Q()
    for private_cidr in PRIVATE_NETWORK_CIDRS:
        network = ipaddress.ip_network(private_cidr)
        min_ip = int(network.network_address)
        max_ip = int(network.broadcast_address)
        filter_ |= Q(min_ip__gte=min_ip, max_ip__lte=max_ip)
    return filter_
PRIVATE_NETWORK_FILTER = get_private_network_filter()


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
            return queryset
        if self.value().lower() == 'private':
            queryset = queryset.filter(PRIVATE_NETWORK_FILTER)
        elif self.value().lower() == 'public':
            queryset = queryset.exclude(PRIVATE_NETWORK_FILTER)
        return queryset


class ContainsIPAddressFilter(TextListFilter):

    title = _('Contains IP address')
    parameter_name = 'contains_ip'

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(ContainsIPAddressFilter, self).__init__(
            field, request, params, model, model_admin, field_path
        )
        self.title = _('Contains IP address')

    def queryset(self, request, queryset):
        filter_str = self.value()
        if not filter_str:
            return queryset

        # Replace all possible separators with spaces
        filter_str = filter_str.translate(
            str.maketrans(
                SEARCH_OR_SEPARATORS,
                ' ' * len(SEARCH_OR_SEPARATORS)
            )
        )

        filter_query = Q()

        for str_addr in filter_str.split(' '):
            try:
                address = int(ipaddress.ip_address(str_addr))
            except ValueError:
                return queryset

            filter_query = filter_query | Q(
                min_ip__lte=address,
                max_ip__gte=address
            )

        queryset = queryset.filter(filter_query)

        return queryset
