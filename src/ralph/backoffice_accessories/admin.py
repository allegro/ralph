from django.utils.translation import ugettext_lazy as _

from ralph.accesories.models import accessories
from ralph.admin import RalphAdmin, register
from ralph.lib.transitions.admin import TransitionAdminMixin

@register(Accessories)
class AccessoriesAdmin(TransitionAdminMixin, RalphAdmin):
    show_transition_history = True
    list_display = ['status', 'manufacturer', 'accessories_name', 'user',
                    'produckt_number', 'number_bought']
    list_select_related = ['user', 'owner']
    raw_id_fields = ['user', 'owner', 'region']
    list_filter = ['status', 'manufacturer', 'accessories_name',
                   'produckt_number', 'user', 'owner', 'user__segment',
                   'user__company', 'user__department']
    search_fields = ['manufacturer', 'accessories_name', 'user__first_name',
                     'user__last_name', 'user__username', 'produckt_number']

    fieldsets = (
        (
            _('Accessories Info'),
            {
                'fields': ('manufacturer', 'accessories_name', 'accessories_type',
                           'produckt_number', 'region', 'warehouse', 'number_bought')
            }
        ),
        (
            _('User Info'),
            {
                'fields': ('user', 'owner', )
            }
        ),
    )
