from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin
from ralph.deployment.forms import PrebootConfigurationForm
from ralph.deployment.models import (
    Deployment,
    Preboot,
    PrebootConfiguration,
    PrebootFile,
    PrebootItem
)


@register(PrebootItem)
class PrebootItemAdmin(RalphAdmin):
    search_fields = ["name"]


@register(PrebootConfiguration)
class PrebootConfigurationAdmin(PrebootItemAdmin):
    form = PrebootConfigurationForm
    fieldsets = (
        (_("Basic info"), {"fields": ("name", "type", "configuration")}),
        (_("Additional info"), {"fields": ("description",)}),
    )
    list_filter = ["type"]
    list_display = ["name", "type", "description"]


@register(PrebootFile)
class PrebootFileAdmin(PrebootItemAdmin):
    fieldsets = (
        (_("Basic info"), {"fields": ("name", "type", "file")}),
        (_("Additional info"), {"fields": ("description",)}),
    )
    list_filter = ["type"]
    list_display = ["name", "type", "description"]


@register(Preboot)
class PrebootAdmin(RalphAdmin):
    raw_id_fields = ["items"]

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "items",
                    "warning_after",
                    "critical_after",
                    "disappears_after",
                )
            },
        ),
        (_("Additional info"), {"fields": ("description",)}),
    )
    list_display = ["name", "description", "used_counter"]
    search_fields = ["name", "description"]
    list_filter = ["name"]


@register(Deployment)
class DeploymentAdmin(RalphAdmin):
    pass
