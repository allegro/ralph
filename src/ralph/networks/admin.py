from urllib.parse import urlencode

from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from ralph.admin import RalphAdmin, register
from ralph.admin.filters import RelatedAutocompleteFieldListFilter
from ralph.admin.mixins import RalphAdminFormMixin
from ralph.data_importer import resources
from ralph.lib.mixins.admin import ParentChangeMixin
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


class AddNetworkForm(RalphAdminFormMixin, ModelForm):
    top_margin = forms.IntegerField()
    bottom_margin = forms.IntegerField()

    class Meta:
        model = Network
        exclude = ('parent',)


@register(Network)
class NetworkAdmin(RalphAdmin):

    def subnetwork(self, obj):
        return '<a href="{}?{}">{} ({})</a>'.format(
            reverse('admin:networks_network_changelist'),
            urlencode({'parent': obj.pk}),
            _('Show'),
            obj.get_descendant_count()
        )

    subnetwork.short_description = 'Subnetwork'
    subnetwork.allow_tags = True

    def name(self, obj):
        return obj.name
    name.short_description = _('Name')
    name.admin_order_field = ['name']

    def address(self, obj):
        return obj.address
    address.short_description = _('Network address')
    address.admin_order_field = ['min_ip']

    change_list_template = 'networks/network_change_list.html'
    change_form_template = 'admin/data_center/network/change_form.html'
    search_fields = ['address', 'remarks']
    list_display = ['name', 'subnetwork', 'address', 'kind', 'vlan']
    list_filter = ['kind', 'dhcp_broadcast',
        ('parent', RelatedAutocompleteFieldListFilter)
    ]  # noqa add rack when multi widget will be available
    raw_id_fields = ['racks', 'terminators']
    resource_class = resources.NetworkResource
    # TODO: adapt form to handle change action
    add_form = AddNetworkForm

    add_message = _('Network added to <a href="{}" _target="blank">{}</a>')
    change_message = _('Network reassigned from network <a href="{}" target="_blank">{}</a> to <a href="{}" target="_blank">{}</a>')  # noqa

    # address.admin_order_field = 'number'

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
            extra_context.update({'parent': parent})

        return super().changelist_view(request, extra_context)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        parent = request.GET.get('parent', None)
        queryset = queryset.filter(parent=parent)
        return queryset


@register(IPAddress)
class IPAddressAdmin(ParentChangeMixin, RalphAdmin):
    search_fields = ['address']
    list_filter = ['is_public', 'is_management']
    list_display = ['address', 'hostname', 'base_object_link', 'is_gateway']
    readonly_fields = ['get_network_path', 'is_public']
    list_select_related = ['base_object']
    raw_id_fields = ['base_object']
    resource_class = resources.IPAddressResource
    list_select_related = ['base_object__content_type']

    fieldsets = (
        (_('Basic info'), {
            'fields': [
                'address', 'get_network_path', 'base_object',
            ]
        }),
        (_('Additional info'), {
            'fields': [
                'hostname', 'is_management', 'is_public'
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

    def base_object_link(self, obj):
        if not obj.base_object:
            return '&ndash;'
        ct = obj.base_object.content_type
        return '<a href="{}" target="_blank">{} ({})</a>'.format(
            reverse('admin:view_on_site', args=(ct.id, obj.base_object.id)),
            ct.model_class()._meta.verbose_name.capitalize(),
            obj.base_object.id,
        )
    base_object_link.short_description = _('Linked object')
    base_object_link.allow_tags = True
