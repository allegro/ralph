from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphTabularInline
from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.models.components import Ethernet
from ralph.networks.forms import NetworkForm, NetworkInlineFormset
from ralph.networks.models import Network


class NetworkInline(RalphTabularInline):
    form = NetworkForm
    formset = NetworkInlineFormset
    model = Ethernet
    exclude = ['model']





#TODO:: rm it
#from django import forms
#from ralph.networks.models import Network
#from django.forms.models import BaseInlineFormSet
#class NetworkForm2(forms.ModelForm):
#    class Meta:
#        model = Network
#        fields = [
#            'remarks',
#        ]
#class NetworkInlineFormset2(BaseInlineFormSet):
#    pass
#class XXXInline(RalphTabularInline):
#    form = NetworkForm2
#    formset = NetworkInlineFormset2
#    model = Network
#    #exclude = ['model']
#
#    #def get_queryset(self, request):
#    #    pass
#    #    import ipdb
#    #    ipdb.set_trace()




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

    inlines = [
        NetworkInline,
    ]


class NetworkWithTerminatorsView(NetworkView):
    inlines = [
        NetworkInline,
        #XXXInline,
        NetworkTerminatorReadOnlyInline,
    ]
    template_name = 'data_center/datacenterasset/networks.html'

    def dispatch(self, request, model, pk, *args, **kwargs):
        result = super().dispatch(request, model, pk, *args, **kwargs)
        self.network_data = self.network_data()
        return result

    def network_data(self, **kwargs):
        return {
            'networks': self.object._get_available_networks(),
            'network_envs': self.object._get_available_network_environments(),
        }
