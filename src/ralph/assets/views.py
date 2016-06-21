from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.models.components import GenericComponent, Memory


class ComponentsAdminView(RalphDetailViewAdmin):
    icon = 'folder'
    name = 'components'
    label = _('Components')
    url_name = 'components'

    class GenericComponentInline(RalphTabularInline):
        model = GenericComponent
        raw_id_fields = ('model',)
        extra = 1

    class MemoryInline(RalphTabularInline):
        model = Memory
        # TODO: discuss model field
        fields = ('label', 'size', 'speed', 'slot_no')
        extra = 1

    inlines = [GenericComponentInline, MemoryInline]
