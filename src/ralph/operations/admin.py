# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphMPTTAdmin, register
from ralph.admin.mixins import RalphAdminForm
from ralph.admin.views.main import RalphChangeList
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer import resources
from ralph.operations.filters import StatusFilter
from ralph.operations.models import (
    Change,
    Failure,
    Incident,
    Operation,
    OperationStatus,
    OperationType,
    Problem
)


class OperationChangeList(RalphChangeList):

    def get_filters(self, request):
        """Avoid using DISTINCT clause when base object filter is not used."""

        filter_specs, filter_specs_exist, lookup_params, use_distinct = \
            super(RalphChangeList, self).get_filters(request)

        filter_params = self.get_filters_params()

        return (
            filter_specs,
            filter_specs_exist,
            lookup_params,
            use_distinct if filter_params.get('base_objects') else False
        )


@register(OperationType)
class OperationTypeAdmin(RalphMPTTAdmin):
    list_display = ('name', 'parent')
    list_select_related = ('parent',)
    search_fields = ['name']

    def has_delete_permission(self, request, obj=None):
        # disable delete
        return False


@register(OperationStatus)
class OperationStatusAdmin(RalphAdmin):
    list_display = ('name',)
    search_fields = ['name']


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
    list_filter = ['type', ('status', StatusFilter), 'reporter',
                   'assignee', 'ticket_id', 'created_date',
                   'update_date', 'resolved_date', 'base_objects']
    list_display = ['title', 'type', 'created_date', 'status', 'reporter',
                    'get_ticket_url']
    list_select_related = ('reporter', 'type', 'status')
    raw_id_fields = ['assignee', 'reporter', 'base_objects']
    resource_class = resources.OperationResource
    form = OperationAdminForm

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'type', 'title', 'status', 'reporter', 'assignee',
                'description', 'ticket_id', 'created_date', 'update_date',
                'resolved_date',
            )
        }),
        (_('Objects'), {
            'fields': (
                'base_objects',
            )
        }),
    )

    def get_ticket_url(self, obj):
        return '<a href="{ticket_url}" target="_blank">{ticket_id}</a>'.format(
            ticket_url=obj.ticket_url,
            ticket_id=obj.ticket_id
        )
    get_ticket_url.allow_tags = True
    get_ticket_url.short_description = _('ticket ID')

    def get_changelist(self, request, **kwargs):
        return OperationChangeList


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
    list_filter = OperationAdmin.list_filter + [
        'base_objects__asset__model__manufacturer'
    ]
