# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphMPTTAdmin, register
from ralph.admin.mixins import RalphAdminForm
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer import resources
from ralph.operations.models import (
    Change,
    Failure,
    Incident,
    Operation,
    OperationType,
    Problem
)


@register(OperationType)
class OperationTypeAdmin(RalphMPTTAdmin):
    list_display = ('name', 'parent')
    list_select_related = ('parent',)
    search_fields = ['name']

    def has_delete_permission(self, request, obj=None):
        # disable delete
        return False


class OperationAdminForm(RalphAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _operation_type_subtree = self.instance._operation_type_subtree
        if _operation_type_subtree:
            root = OperationType.objects.get(pk=_operation_type_subtree)
            self.fields['type'].queryset = self.fields['type'].queryset.filter(
                pk__in=root.get_descendants(include_self=True)
            )


@register(Operation)
class OperationAdmin(AttachmentsMixin, RalphAdmin):
    search_fields = ['title', 'description', 'ticket_id']
    list_filter = ['type', 'status']
    list_display = ['title', 'type', 'status', 'asignee', 'issue_url']
    raw_id_fields = ['asignee', 'base_objects']
    resource_class = resources.OperationResource
    form = OperationAdminForm

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'type', 'title', 'status', 'asignee', 'description',
                'ticket_id', 'created_date', 'update_date', 'resolved_date',
            )
        }),
        (_('Objects'), {
            'fields': (
                'base_objects',
            )
        }),
    )

    def issue_url(self, obj):
        return '<a href="{issue_tracker}{issue_id}" target="_blank">{issue_id}</a>'.format(  # noqa
            issue_tracker=settings.ISSUE_TRACKER_URL,
            issue_id=obj.ticket_id
        )
    issue_url.allow_tags = True
    issue_url.short_description = _('Issue')


@register(Change)
class ChangeAdmin(OperationAdmin):
    pass


@register(Incident)
class IncidentAdmin(OperationAdmin):
    pass


@register(Problem)
class ProblemAdmin(OperationAdmin):
    pass


@register(Failure)
class FailureAdmin(OperationAdmin):
    pass
