from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.admin.m2m import RalphTabularM2MInline
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.operations.models import Operation


class OperationInline(RalphTabularM2MInline):
    model = Operation
    raw_id_fields = ('asignee',)
    fields = ('title', 'description', 'asignee', 'type', 'status', 'ticket_id')
    extra = 1
    verbose_name = _('Operation')

    widgets = {
        'description': forms.Textarea(attrs={'rows': 2, 'cols': 30}),
    }

    def get_formset(self, *args, **kwargs):
        kwargs.setdefault('widgets', {}).update(self.widgets)
        return super().get_formset(*args, **kwargs)


class OperationInlineReadOnlyForExisting(OperationInline):
    extra = 0
    show_change_link = True
    verbose_name_plural = _('Existing Operations')

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def has_add_permission(self, request):
        return False


class OperationInlineAddOnly(OperationInline):
    can_delete = False
    verbose_name_plural = _('Add new Operations')

    def has_change_permission(self, request, obj=None):
        return False


class OperationView(RalphDetailViewAdmin):
    """
    Regular inline (form for new and existing Operations)
    """
    icon = 'ambulance'
    label = _('Operations')
    inlines = [OperationInline]


class OperationViewReadOnlyForExisiting(OperationView):
    """
    Form for adding new Operations, read-only table for exising Operations
    """
    inlines = [OperationInlineAddOnly, OperationInlineReadOnlyForExisting]
