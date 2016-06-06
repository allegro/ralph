from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.deployment.forms import PrebootConfigurationForm
from ralph.deployment.models import (
    Preboot,
    PrebootConfiguration,
    PrebootFile,
    PrebootItem
)


@register(PrebootItem)
class PrebootItemAdmin(RalphAdmin):
    search_fields = ['name']


@register(PrebootConfiguration)
class PrebootConfigurationAdmin(PrebootItemAdmin):
    form = PrebootConfigurationForm
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'type', 'configuration'
            )
        }),
        (_('Additional info'), {
            'fields': (
                'description',
            )
        }),
    )


@register(PrebootFile)
class PrebootFileAdmin(PrebootItemAdmin):
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'type', 'file'
            )
        }),
        (_('Additional info'), {
            'fields': (
                'description',
            )
        }),
    )


@register(Preboot)
class PrebootAdmin(RalphAdmin):
    raw_id_fields = ['items']

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'name', 'items'
            )
        }),
        (_('Additional info'), {
            'fields': (
                'description',
            )
        }),
    )
