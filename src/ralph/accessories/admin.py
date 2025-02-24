from django.utils.translation import ugettext_lazy as _

from ralph.accessories.models import Accessory, AccessoryUser
from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin, RalphTabularInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.lib.transitions.admin import TransitionAdminMixin


class AccessoryUserView(RalphDetailViewAdmin):
    icon = "user"
    name = "users"
    label = _("Assigned to users")
    url_name = "assigned-to-users"

    class AccessoryUserInline(RalphTabularInline):
        model = AccessoryUser
        raw_id_fields = ("user",)
        extra = 1

    inlines = [AccessoryUserInline]


@register(Accessory)
class AccessoryAdmin(TransitionAdminMixin, RalphAdmin):
    show_transition_history = True
    list_display = [
        "status",
        "manufacturer",
        "accessory_name",
        "product_number",
        "number_bought",
        "free",
    ]
    readonly_fields = ["used", "free"]
    list_select_related = ["owner"]
    raw_id_fields = ["owner", "region"]
    list_filter = [
        "status",
        "manufacturer",
        "accessory_name",
        "product_number",
        "warehouse",
    ]
    change_views = [
        AccessoryUserView,
    ]
    search_fields = ["accessory_name", "product_number"]

    fieldsets = (
        (
            _("Accessory Info"),
            {
                "fields": (
                    "manufacturer",
                    "accessory_name",
                    "category",
                    "product_number",
                    "region",
                    "warehouse",
                    "number_bought",
                    "used",
                    "free",
                )
            },
        ),
        (_("User Info"), {"fields": ("owner",)}),
    )
