from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphTabularInline
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.models.components import Ethernet
from ralph.lib.table import TableWithUrl
from ralph.networks.forms import NetworkForm, NetworkInlineFormset
from ralph.networks.models import Network


class NetworkInline(RalphTabularInline):
    form = NetworkForm
    formset = NetworkInlineFormset
    model = Ethernet
    exclude = ['model']


class NetworkTerminatorReadOnlyInline(RalphTabularM2MInline):
    model = Network
    extra = 0
    show_change_link = True
    verbose_name_plural = _('Terminators of')
    fields = [
        'name', 'address',
    ]

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def has_add_permission(self, request):
        return False


class NetworkView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'Network'
    url_name = 'network'
    admin_attribute_list_to_copy = ['available_networks', 'available_environments']
    readonly_fields = ('available_networks', 'available_environments')
    inlines = [
        NetworkInline,
    ]
    fieldsets = (
        (_(''), {
            'fields': (
                'available_networks',
            )
        }),
        (_(''), {
            'fields': (
                'available_environments',
            )
        }),
    )

    def available_networks(self, instance):
        networks = instance._get_available_networks(
            as_query=True
        ).select_related('network_environment')
        if networks:
            result = TableWithUrl(
                networks,
                ['name', 'address', 'network_environment', 'get_first_free_ip'],
                url_field='name',
            ).render()
        else:
            result = '&ndash;'
        return result
    available_networks.short_description = _('Available networks')
    available_networks.allow_tags = True

    def available_environments(self, instance):
        network_envs = instance._get_available_network_environments(as_query=True)
        if network_envs:
            result = TableWithUrl(
                network_envs,
                [('name', 'Environment'), 'get_next_free_hostname'],
                url_field='name',
            ).render()
        else:
            result = '&ndash;'
        return result
    available_environments.short_description = _('Available network environments')
    available_environments.allow_tags = True


class NetworkWithTerminatorsView(NetworkView):
    inlines = [
        NetworkInline,
        NetworkTerminatorReadOnlyInline,
    ]
