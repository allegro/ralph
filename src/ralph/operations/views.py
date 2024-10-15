from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.operations.models import Operation


class OperationInline(RalphTabularM2MInline):
    model = Operation
    raw_id_fields = ("assignee", "reporter")
    fields = ["title", "description", "reporter", "type", "status", "ticket_id"]
    extra = 1
    verbose_name = _("Operation")

    widgets = {
        "description": forms.Textarea(attrs={"rows": 2, "cols": 30}),
    }

    def get_formset(self, *args, **kwargs):
        kwargs.setdefault("widgets", {}).update(self.widgets)
        return super().get_formset(*args, **kwargs)


class OperationInlineReadOnlyForExisting(OperationInline):
    extra = 0
    show_change_link = True
    verbose_name_plural = _("Existing Operations")
    fields = ["title", "description", "reporter", "type", "status", "get_ticket_url"]

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def has_add_permission(self, request):
        return False

    @mark_safe
    def get_ticket_url(self, obj):
        return '<a href="{ticket_url}" target="_blank">{ticket_id}</a>'.format(
            ticket_url=obj.ticket_url, ticket_id=obj.ticket_id
        )

    get_ticket_url.short_description = _("ticket ID")


class OperationInlineAddOnly(OperationInline):
    can_delete = False
    verbose_name_plural = _("Add new Operation")
    fields = ["title", "description", "type", "status", "ticket_id"]

    def has_change_permission(self, request, obj=None):
        return False


class OperationView(RalphDetailViewAdmin):
    """
    Regular inline (form for new and existing Operations)
    """

    icon = "ambulance"
    label = _("Operations")
    inlines = [OperationInline]


class OperationViewReadOnlyForExisiting(OperationView):
    """
    Form for adding new Operations, read-only table for exising Operations
    """

    inlines = [OperationInlineAddOnly, OperationInlineReadOnlyForExisting]
