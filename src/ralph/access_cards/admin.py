from django.utils.translation import ugettext_lazy as _

from ralph.access_cards.models import AccessCard
from ralph.admin import RalphAdmin, register


@register(AccessCard)
class AccessCardAdmin(RalphAdmin):
    list_display = ['status', 'system_number', 'user', 'owner']
    list_select_related = ['user', 'owner']
    raw_id_fields = ['user', 'owner']
    list_filter = ['status', 'issue_date', 'visual_number',
                   'system_number', 'user', 'owner', 'user__segment',
                   'user__company', 'user__department', 'user__employee_id']
    search_fields = ['visual_number', 'system_number', 'user__first_name',
                     'user__last_name', 'user__username']

    fieldsets = (
        (
            _('Access Card Info'),
            {
                'fields': ('visual_number', 'system_number',
                           'status', 'issue_date', 'notes')
            }
        ),
        (
            _('User Info'),
            {
                'fields': ('user', 'owner')
            }
        )
    )
