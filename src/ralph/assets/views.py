from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.models.components import (
    Disk,
    Ethernet,
    FibreChannelCard,
    Memory,
    Processor
)
from ralph.networks.forms import EthernetLockDeleteForm, NetworkInlineFormset


class ComponentsAdminView(RalphDetailViewAdmin):
    icon = "folder"
    name = "components"
    label = _("Components")
    url_name = "components"

    class MemoryInline(RalphTabularInline):
        model = Memory
        fields = ("model_name", "size", "speed")
        extra = 1

    class FibreChannelCardInline(RalphTabularInline):
        model = FibreChannelCard
        fields = (
            "model_name",
            "speed",
            "wwn",
            "firmware_version",
        )
        extra = 1

    class ProcessorInline(RalphTabularInline):
        model = Processor
        fields = ("model_name", "speed", "cores", "logical_cores")
        extra = 1

    class DiskInline(RalphTabularInline):
        model = Disk
        fields = (
            "model_name",
            "size",
            "serial_number",
            "slot",
            "firmware_version",
        )
        extra = 1

    class EthernetInline(RalphTabularInline):
        model = Ethernet
        fields = ("mac", "model_name", "label", "speed")
        extra = 1
        formset = NetworkInlineFormset
        form = EthernetLockDeleteForm

    inlines = [
        EthernetInline,
        MemoryInline,
        ProcessorInline,
        DiskInline,
        FibreChannelCardInline,
    ]
