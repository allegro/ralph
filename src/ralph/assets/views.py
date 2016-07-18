from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.models.components import (
    Disk,
    FibreChannelCard,
    GenericComponent,
    Memory,
    Processor
)


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
        fields = ('model_name', 'size', 'speed')
        extra = 1

    class FibreChannelCardInline(RalphTabularInline):
        model = FibreChannelCard
        fields = (
            'model_name',
            'speed',
            'wwn',
            'firmware_version',
        )
        extra = 1

    class ProcessorInline(RalphTabularInline):
        model = Processor
        fields = (
            'model_name',
            'speed',
            'cores',
        )
        extra = 1

    class DiskInline(RalphTabularInline):
        model = Disk
        fields = (
            'model_name', 'size', 'serial_number', 'slot', 'firmware_version',
        )
        extra = 1

    inlines = [
        GenericComponentInline,
        MemoryInline,
        FibreChannelCardInline,
        ProcessorInline,
        DiskInline,
    ]
