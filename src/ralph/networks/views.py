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
    admin_attribute_list_to_copy = ['network_data']
    readonly_fields = ('network_data',)
    inlines = [
        NetworkInline,
    ]
    fields = ('network_data', )

    def network_data(self, instance):
        return TableWithUrl(
            instance._get_available_networks(as_query=True),
            ['name', 'address', 'network_environment'],
            url_field='name',
        ).render()
    network_data.short_description = "Network data"
    network_data.allow_tags = True
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'network_data',
            )
        }),
    )


class NetworkWithTerminatorsView(NetworkView):
    inlines = [
        NetworkInline,
        NetworkTerminatorReadOnlyInline,
    ]
