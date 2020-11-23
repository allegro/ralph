from django.utils.translation import ugettext_lazy as _

from ralph.accessories.models import Accessories, AccessoriesUser
from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.lib.transitions.admin import TransitionAdminMixin


class AccessoriesUserView(RalphDetailViewAdmin):
    icon = 'user'
    name = 'users'
    label = _('Assigned to users')
    url_name = 'assigned-to-users'

    class AccessoriesUserInline(RalphTabularInline):
        model = AccessoriesUser
        raw_id_fields = ('user',)
        extra = 1

    inlines = [AccessoriesUserInline]


@register(Accessories)
class AccessoriesAdmin(TransitionAdminMixin, RalphAdmin):
    show_transition_history = True
    list_display = ['status', 'manufacturer', 'accessories_name',
                    'user', 'product_number', 'number_bought']
    readonly_fields = ['used', 'free']
    list_select_related = ['user', 'owner']
    raw_id_fields = ['user', 'owner', 'region']
    list_filter = ['status', 'manufacturer', 'accessories_name',
                   'product_number', 'user', 'owner', 'user__segment',
                   'user__company', 'user__department']
    change_views = [AccessoriesUserView, ]
    search_fields = ['manufacturer', 'accessories_name',
                     'user__first_name', 'user__last_name', 'user__username',
                     'product_number']

    fieldsets = (
        (
            _('Accessories Info'),
            {
                'fields': ('manufacturer', 'accessories_name',
                           'accessories_type', 'product_number',
                           'region', 'warehouse', 'number_bought',
                           'free', 'used',)
            }
        ),
        (
            _('User Info'),
            {
                'fields': ('user', 'owner', )
            }
        ),
    )
