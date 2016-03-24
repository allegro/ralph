from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.admin.filters import RelatedAutocompleteFieldListFilter
from ralph.admin.mixins import RalphAdminFormMixin
from ralph.assets.models import BaseObject
from ralph.data_importer import resources
from ralph.lib.mixins.admin import ParentChangeMixin
from ralph.lib.table import TableWithUrl
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


@register(Network)
class NetworkAdmin(RalphAdmin):
    change_list_template = 'networks/network_change_list.html'
    change_form_template = 'admin/data_center/network/change_form.html'
    search_fields = ['address', 'remarks']
    list_display = [
        'name', 'subnetwork', 'address', 'kind', 'vlan', 'network_environment'
    ]
    list_filter = [
        'kind', 'dhcp_broadcast', 'racks', 'terminators', 'service_env',
        ('parent', RelatedAutocompleteFieldListFilter)
    ]
    list_select_related = ['kind']
    raw_id_fields = ['racks', 'terminators']
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

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        parent = request.GET.get('parent', None)
        if parent:
            parent = Network.objects.get(pk=parent)
            extra_context.update(
                {'parents_network': parent.get_ancestors(include_self=True)}
            )

        return super().changelist_view(request, extra_context)

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

    def subnetwork(self, obj):
        count = obj.get_descendant_count()
        if count:
            return '<a href="{}?{}">{} ({})</a>'.format(
                reverse('admin:networks_network_changelist'),
                urlencode({'parent': obj.pk}),
                _('Show'),
                count
            )
        return ''

    subnetwork.short_description = 'Subnetwork'
    subnetwork.allow_tags = True

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
        return ' > '.join(nodes_link)
    show_parent_networks.short_description = _('Parent networks')
    show_parent_networks.allow_tags = True

    def show_subnetworks(self, network):
        if not network or not network.pk:
            return '&ndash;'
        return TableWithUrl(
            network.get_subnetworks().order_by('min_ip'), ['name', 'address']
        ).render()
    show_subnetworks.allow_tags = True
    show_subnetworks.short_description = _('Subnetworks')

    def show_addresses(self, network):
        if not network or not network.pk:
            return '&ndash;'
        return TableWithUrl(
            IPAddress.objects.filter(network=network).order_by('number'),
            ['address', 'hostname']
        ).render()
    show_addresses.allow_tags = True
    show_addresses.short_description = _('Addresses')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        parent = request.GET.get('parent', None)
        queryset = queryset.filter(parent=parent)
        return queryset


@register(IPAddress)
class IPAddressAdmin(ParentChangeMixin, RalphAdmin):
    search_fields = ['address']
    list_filter = ['is_public', 'is_management']
    list_display = [
        'address', 'hostname', 'base_object_link', 'is_gateway', 'is_public'
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

    def base_object_link(self, obj):
        if not obj.base_object:
            return '&ndash;'
        return '<a href="{}" target="_blank">{}</a>'.format(
            reverse('admin:view_on_site', args=(
                obj.base_object.content_type_id,
                obj.base_object_id
            )),
            obj.base_object._str_with_type,
        )
    base_object_link.short_description = _('Linked object')
    base_object_link.allow_tags = True
