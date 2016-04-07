from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.filters import RelatedAutocompleteFieldListFilter
from ralph.admin.mixins import RalphAdminFormMixin, RalphMPTTAdmin
from ralph.admin.views.main import RalphChangeList
from ralph.assets.models import BaseObject
from ralph.data_importer import resources
from ralph.lib.mixins.admin import ParentChangeMixin
from ralph.lib.table import TableWithUrl
from ralph.networks.filters import IPRangeFilter, NetworkRangeFilter
from ralph.networks.models.networks import (
    DiscoveryQueue,
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)


@register(NetworkEnvironment)
class NetworkEnvironmentAdmin(RalphAdmin):
    pass


@register(NetworkKind)
class NetworkKindAdmin(RalphAdmin):
    pass


@register(DiscoveryQueue)
class DiscoveryQueueAdmin(RalphAdmin):
    pass


class NetworkForm(RalphAdminFormMixin, ModelForm):
    top_margin = forms.IntegerField(initial=settings.DEFAULT_NETWORK_MARGIN)
    bottom_margin = forms.IntegerField(initial=settings.DEFAULT_NETWORK_MARGIN)

    class Meta:
        model = Network
        exclude = ('parent',)


def ip_address_base_object_link(obj):
    if not obj.base_object:
        return '&ndash;'
    return '<a href="{}" target="_blank">{}</a>'.format(
        reverse('admin:view_on_site', args=(
            obj.base_object.content_type_id,
            obj.base_object_id
        )),
        obj.base_object._str_with_type,
    )


class LinkedObjectTable(TableWithUrl):

    def linked_object(self, item):
        return ip_address_base_object_link(item)

    linked_object.title = _('Linked object')


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
        filter_params = self.get_filters_params()
        if filter_params:
            self.model_admin.mptt_indent_field = 10
        else:
            self.model_admin.mptt_indent_field = 0
        return queryset


@register(Network)
class NetworkAdmin(RalphMPTTAdmin):
    change_form_template = 'admin/data_center/network/change_form.html'
    search_fields = ['address', 'remarks']
    list_display = [
        'name', 'address', 'kind', 'vlan', 'network_environment'
    ]
    list_filter = [
        'kind', 'dhcp_broadcast', 'racks', 'terminators', 'service_env',
        ('parent', RelatedAutocompleteFieldListFilter),
        ('min_ip', NetworkRangeFilter)
    ]
    list_select_related = ['kind', 'network_environment']
    raw_id_fields = ['racks', 'terminators', 'service_env']
    resource_class = resources.NetworkResource
    readonly_fields = [
        'show_subnetworks', 'show_addresses', 'show_parent_networks'
    ]
    # TODO: adapt form to handle change action
    form = NetworkForm

    add_message = _('Network added to <a href="{}" _target="blank">{}</a>')
    change_message = _('Network reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>')  # noqa

    fieldsets = (
        (_('Basic info'), {
            'fields': [
                'name', 'address', 'remarks', 'terminators', 'vlan', 'racks',
                'network_environment', 'kind', 'service_env', 'dhcp_broadcast',
                'top_margin', 'bottom_margin'
            ]
        }),
        (_('Relations'), {
            'fields': [
                'show_parent_networks', 'show_subnetworks', 'show_addresses'
            ]
        })
    )

    def get_changelist(self, request, **kwargs):
        return NetworkRalphChangeList

    def changeform_view(
        self, request, object_id=None, form_url='', extra_context=None
    ):
        if not extra_context:
            extra_context = {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['next_free_ip'] = obj.get_first_free_ip()
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        bottom_margin = form.cleaned_data.get('bottom_margin', None)
        top_margin = form.cleaned_data.get('top_margin', None)
        obj.save()
        if bottom_margin and top_margin:
            obj.reserve_margin_addresses(
                bottom_count=form.cleaned_data['bottom_margin'],
                top_count=form.cleaned_data['top_margin'],
            )

    def address(self, obj):
        return obj.address
    address.short_description = _('Network address')
    address.admin_order_field = ['min_ip']

    def show_parent_networks(self, network):
        if not network or not network.pk:
            return '&ndash;'
        nodes = network.get_ancestors(include_self=False)
        nodes_link = []
        for node in nodes:
            nodes_link.append('<a href="{}" target="blank">{}</a>'.format(
                node.get_absolute_url(), node
            ))
        return ' <br /> '.join(nodes_link)
    show_parent_networks.short_description = _('Parent networks')
    show_parent_networks.allow_tags = True

    def show_subnetworks(self, network):
        if not network or not network.pk:
            return '&ndash;'

        return TableWithUrl(
            network.get_subnetworks().order_by('min_ip'),
            ['name', 'address'],
            url_field='name'
        ).render()
    show_subnetworks.allow_tags = True
    show_subnetworks.short_description = _('Subnetworks')

    def show_addresses(self, network):
        if not network or not network.pk:
            return '&ndash;'

        return LinkedObjectTable(
            IPAddress.objects.filter(network=network).order_by('number'),
            ['address', 'linked_object'],
            url_field='address'
        ).render()
    show_addresses.allow_tags = True
    show_addresses.short_description = _('Addresses')

    def get_paginator(
        self, request, queryset, per_page, orphans=0,
        allow_empty_first_page=True
    ):
        # Return all count found records because we want
        # display the tree mptt correctly for all networks.
        per_page = queryset.count()
        return self.paginator(
            queryset, per_page, orphans, allow_empty_first_page
        )


@register(IPAddress)
class IPAddressAdmin(ParentChangeMixin, RalphAdmin):
    search_fields = ['address']
    list_filter = ['is_public', 'is_management', ('address', IPRangeFilter)]
    list_display = [
        'ip_address', 'hostname', 'base_object_link', 'is_gateway',
        'is_public'
    ]
    readonly_fields = ['get_network_path', 'is_public', 'is_gateway']
    raw_id_fields = ['base_object']
    resource_class = resources.IPAddressResource

    fieldsets = (
        (_('Basic info'), {
            'fields': [
                'address', 'get_network_path', 'status', 'base_object',
            ]
        }),
        (_('Additional info'), {
            'fields': [
                'hostname', 'is_management', 'is_public', 'is_gateway'
            ]
        }),
    )

    add_message = _('IP added to <a href="{}" _target="blank">{}</a>')
    change_message = _('IP reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>')  # noqa

    def get_network_path(self, obj):
        if not obj.network:
            return None
        nodes = obj.network.get_ancestors(include_self=True)
        nodes_link = []
        for node in nodes:
            nodes_link.append('<a href="{}" target="blank">{}</a>'.format(
                node.get_absolute_url(), node
            ))
        return ' > '.join(nodes_link)
    get_network_path.short_description = _('Network')
    get_network_path.allow_tags = True

    def get_queryset(self, request):
        # use Prefetch like select-related to get base_objects with custom
        # queryset (to get final model, not only BaseObject)
        return super().get_queryset(request).prefetch_related(Prefetch(
            'base_object',
            queryset=BaseObject.polymorphic_objects.all())
        )

    def ip_address(self, obj):
        return '<a href="{}" target="blank">{}</a>'.format(
            obj.get_absolute_url(), obj.address
        )

    ip_address.short_description = _('IP address')
    ip_address.admin_order_field = 'number'
    ip_address.allow_tags = True

    def base_object_link(self, obj):
        return ip_address_base_object_link(obj)
    base_object_link.short_description = _('Linked object')
    base_object_link.allow_tags = True
