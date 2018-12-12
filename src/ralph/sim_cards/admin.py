from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.sim_cards.models import CellularCarrier, SIMCard


@register(SIMCard)
class SIMCardAdmin(RalphAdmin):
    # NOTE(Anna Gabler): list_display - list on top page
    #                    raw_id_fields - fancy autocomplete
    #                    list_select_related - join to database (DJANGO)
    #                    list_filter  - list of filters on simcard list
    #                    fieldsets - configuration of editor layout
    list_display = ['status', 'card_number', 'phone_number', 'pin1', 'puk1',
                    'user', 'owner', 'warehouse', 'carrier',
                    'quarantine_until']
    raw_id_fields = ['warehouse', 'owner', 'user', 'carrier']

    list_select_related = [
        'user', 'warehouse', 'owner', 'carrier'
    ]

    list_filter = [
        'status', 'card_number', 'warehouse', 'user', 'owner', 'user__segment',
        'user__company', 'user__department', 'user__employee_id', 'carrier',
        'quarantine_until'
    ]

    fieldsets = (
        (_('SIM Card Info'), {
            'fields': (
                'status', 'card_number', 'phone_number', 'pin1', 'puk1',
                'pin2', 'puk2', 'carrier', 'remarks'
            )
        }),
        (_('User Info'), {
            'fields': (
                'user', 'owner', 'warehouse', 'quarantine_until'
            )
        }),
    )


@register(CellularCarrier)
class CellularCarrierAdmin(RalphAdmin):
    list_display = ['name']
