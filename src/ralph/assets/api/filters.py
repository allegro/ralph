import django_filters


class NetworkableObjectFilters(django_filters.FilterSet):
    """
    Base filter for all networkable objects for example with IP address.
    """

    configuration_path = django_filters.CharFilter(
        field_name="configuration_path__path"
    )
    ip = django_filters.CharFilter(field_name="ethernet_set__ipaddress__address")

    class Meta:
        fields = [
            "configuration_path__module__name",
        ]
