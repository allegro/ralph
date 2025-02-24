from django.contrib.admin.views.main import ORDER_VAR, SEARCH_VAR
from django.db.models import Count, F, Prefetch
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import RelatedAutocompleteFieldListFilter
from ralph.admin.helpers import CastToInteger
from ralph.admin.mixins import RalphAdmin, RalphMPTTAdmin
from ralph.admin.views.main import RalphChangeList
from ralph.assets.models import BaseObject
from ralph.data_importer import resources
from ralph.lib.mixins.admin import ParentChangeMixin
from ralph.lib.table.table import TableWithUrl
from ralph.networks.filters import (
    ContainsIPAddressFilter,
    IPRangeFilter,
    NetworkClassFilter,
    NetworkRangeFilter
)
from ralph.networks.models.networks import (
    DiscoveryQueue,
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)


@register(NetworkEnvironment)
class NetworkEnvironmentAdmin(RalphAdmin):
    list_display = ["name", "data_center", "use_hostname_counter"]
    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": [
                    "name",
                    "data_center",
                    "domain",
                    "remarks",
                    "use_hostname_counter",
                ],
            },
        ),
        (
            _("Hostnames"),
            {
                "fields": [
                    "hostname_template_counter_length",
                    "hostname_template_prefix",
                    "hostname_template_postfix",
                    "next_free_hostname",
                ],
            },
        ),
    )
    readonly_fields = ["next_free_hostname"]
    search_fields = ["name"]
    list_filter = ["data_center"]


@register(NetworkKind)
class NetworkKindAdmin(RalphAdmin):
    search_fields = ["name"]


@register(DiscoveryQueue)
class DiscoveryQueueAdmin(RalphAdmin):
    pass


def ip_address_base_object_link(obj):
    if not obj.base_object:
        return "&ndash;"
    link = '<a href="{}" target="_blank">{}</a>'.format(
        reverse(
            "admin:view_on_site",
            args=(obj.base_object.content_type_id, obj.base_object.id),
        ),
        escape(obj.base_object._str_with_type),
    )
    return link


class LinkedObjectTable(TableWithUrl):
    def linked_object(self, item):
        return ip_address_base_object_link(item)

    linked_object.title = _("Linked object")


class NetworkRalphChangeList(RalphChangeList):
    def get_queryset(self, request):
        """
        Check if it has been used any filter,
        if yes change mptt_indent_field value in model_admin to '0'
        so as not to generate a tree list

        Args:
            request: Django Request object

        Returns:
            Django queryset
        """
        queryset = super().get_queryset(request)
        any_params = (
            self.get_filters_params()
            or self.params.get(SEARCH_VAR)
            or self.params.get(ORDER_VAR)
        )
        if any_params:
            self.model_admin.mptt_indent_field = 10
        else:
            self.model_admin.mptt_indent_field = 0
        return queryset


@register(Network)
class NetworkAdmin(RalphMPTTAdmin):
    ordering = ["min_ip", "-max_ip"]
    change_form_template = "admin/data_center/network/change_form.html"
    search_fields = ["name", "address", "remarks", "vlan"]
    list_display = [
        "name",
        "address",
        "kind",
        "vlan",
        "network_environment",
        "subnetworks_count",
        "ipaddresses_count",
    ]
    list_filter = [
        "network_environment",
        "kind",
        "dhcp_broadcast",
        "racks",
        "terminators",
        "service_env",
        "vlan",
        ("parent", RelatedAutocompleteFieldListFilter),
        ("min_ip", NetworkRangeFilter),
        ("address", NetworkClassFilter),
        ("max_ip", ContainsIPAddressFilter),
    ]
    list_select_related = ["kind", "network_environment"]
    raw_id_fields = [
        "racks",
        "gateway",
        "terminators",
        "service_env",
        "dns_servers_group",
    ]
    resource_class = resources.NetworkResource
    readonly_fields = [
        "show_subnetworks",
        "show_addresses",
        "show_parent_networks",
        "show_first_free_ip",
    ]

    add_message = _('Network added to <a href="{}" _target="blank">{}</a>')
    change_message = _(
        'Network reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>'  # noqa
    )

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": [
                    "name",
                    "address",
                    "gateway",
                    "remarks",
                    "terminators",
                    "vlan",
                    "racks",
                    "network_environment",
                    "dns_servers_group",
                    "kind",
                    "service_env",
                    "dhcp_broadcast",
                    "reserved_from_beginning",
                    "reserved_from_end",
                ]
            },
        ),
        (
            _("Relations"),
            {
                "fields": [
                    "show_first_free_ip",
                    "show_parent_networks",
                    "show_subnetworks",
                    "show_addresses",
                ]
            },
        ),
    )

    def get_changelist(self, request, **kwargs):
        return NetworkRalphChangeList

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context["next_free_ip"] = obj.get_first_free_ip()
        return super().changeform_view(request, object_id, form_url, extra_context)

    def address(self, obj):
        return obj.address

    address.short_description = _("Network address")
    address.admin_order_field = ["min_ip", "-max_ip"]

    def subnetworks_count(self, obj):
        return obj.get_descendant_count()

    subnetworks_count.short_description = _("Subnetworks count")
    subnetworks_count.admin_order_field = "subnetworks_count"

    def ipaddresses_count(self, obj):
        return obj.ipaddress_count

    ipaddresses_count.short_description = _("IPAddress count")
    ipaddresses_count.admin_order_field = "ipaddress_count"

    @mark_safe
    def show_parent_networks(self, network):
        if not network or not network.pk:
            return "&ndash;"
        nodes = network.get_ancestors(include_self=False)
        nodes_link = []
        for node in nodes:
            nodes_link.append(
                '<a href="{}" target="blank">{}</a>'.format(
                    node.get_absolute_url(), escape(node)
                )
            )
        return " <br /> ".join(nodes_link)

    show_parent_networks.short_description = _("Parent networks")

    @mark_safe
    def show_first_free_ip(self, network):
        if not network or not network.pk:
            return "&ndash;"
        free_ip = network.get_first_free_ip()
        return str(free_ip) if free_ip else "&ndash;"

    show_first_free_ip.short_description = _("First free IP")

    @mark_safe
    def show_subnetworks(self, network):
        if not network or not network.pk:
            return "&ndash;"

        return TableWithUrl(
            network.get_subnetworks().order_by("min_ip"),
            ["name", "address"],
            url_field="name",
        ).render()

    show_subnetworks.short_description = _("Subnetworks")

    @mark_safe
    def show_addresses(self, network):
        if not network or not network.pk:
            return "&ndash;"

        return LinkedObjectTable(
            IPAddress.objects.filter(network=network)
            .order_by("number")
            .prefetch_related(
                Prefetch(
                    "ethernet__base_object",
                    queryset=BaseObject.polymorphic_objects.all(),
                )
            ),
            ["address", "linked_object"],
            url_field="address",
        ).render()

    show_addresses.short_description = _("Addresses")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Getting subnetwork counts, used for column ordering
        # https://github.com/django-mptt/django-mptt/blob/master/mptt/models.py#L594  # noqa
        qs = qs.annotate(ipaddress_count=Count("ips")).annotate(
            subnetworks_count=(CastToInteger(F("rght")) - CastToInteger(F("lft")))
        )
        return qs

    def get_paginator(
        self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    ):
        # Return all count found records because we want
        # display the tree mptt correctly for all networks.
        per_page = queryset.count()
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)


@register(IPAddress)
class IPAddressAdmin(ParentChangeMixin, RalphAdmin):
    search_fields = ["address", "hostname"]
    ordering = ["number"]
    list_filter = ["hostname", "is_public", "is_management", ("address", IPRangeFilter)]
    list_display = [
        "address",
        "hostname",
        "base_object_link",
        "is_gateway",
        "is_public",
    ]
    readonly_fields = ["get_network_path", "is_public"]
    raw_id_fields = ["ethernet"]
    resource_class = resources.IPAddressResource

    fieldsets = (
        (
            _("Basic info"),
            {"fields": ["address", "get_network_path", "status", "ethernet"]},
        ),
        (
            _("Additional info"),
            {
                "fields": [
                    "hostname",
                    "is_management",
                    "is_public",
                    "is_gateway",
                    "dhcp_expose",
                ]
            },
        ),
    )

    add_message = _('IP added to <a href="{}" _target="blank">{}</a>')
    change_message = _(
        'IP reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>'  # noqa
    )

    @mark_safe
    def get_network_path(self, obj):
        if not obj.network:
            return None
        nodes = obj.network.get_ancestors(include_self=True)
        nodes_link = []
        for node in nodes:
            nodes_link.append(
                '<a href="{}" target="blank">{}</a>'.format(
                    node.get_absolute_url(), escape(node)
                )
            )
        return " > ".join(nodes_link)

    get_network_path.short_description = _("Network")

    def get_queryset(self, request):
        # use Prefetch like select-related to get base_objects with custom
        # queryset (to get final model, not only BaseObject)
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                Prefetch(
                    "ethernet__base_object",
                    queryset=BaseObject.polymorphic_objects.all(),
                )
            )
        )

    @mark_safe
    def ip_address(self, obj):
        return '<a href="{}">{}</a>'.format(obj.get_absolute_url(), escape(obj.address))

    ip_address.short_description = _("IP address")
    ip_address.admin_order_field = "number"

    @mark_safe
    def base_object_link(self, obj):
        return ip_address_base_object_link(obj)

    base_object_link.short_description = _("Linked object")
