# -*- coding: utf-8 -*-
from collections import Counter

from django.db.models import DateTimeField, Prefetch
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin, RalphAdminForm, RalphMPTTAdmin
from ralph.admin.views.main import RalphChangeList
from ralph.admin.widgets import AdminDateTimeWidget
from ralph.assets.models import BaseObject
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

        filter_specs, filter_specs_exist, lookup_params, use_distinct = super(
            RalphChangeList, self
        ).get_filters(request)

        filter_params = self.get_filters_params()

        return (
            filter_specs,
            filter_specs_exist,
            lookup_params,
            use_distinct if filter_params.get("base_objects") else False,
        )


@register(OperationType)
class OperationTypeAdmin(RalphMPTTAdmin):
    list_display = ("name", "parent")
    list_select_related = ("parent",)
    search_fields = ["name"]

    def has_delete_permission(self, request, obj=None):
        # disable delete
        return False


@register(OperationStatus)
class OperationStatusAdmin(RalphAdmin):
    list_display = ("name",)
    search_fields = ["name"]


class OperationAdminForm(RalphAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _operation_type_subtree = self.instance._operation_type_subtree
        if _operation_type_subtree:
            root = OperationType.objects.get(pk=_operation_type_subtree)
            self.fields["type"].queryset = self.fields["type"].queryset.filter(
                pk__in=root.get_descendants(include_self=True)
            )


class ServiceEnvironmentAndConfigurationPathMixin(object):
    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        return list_display + ["get_services", "get_configuration_path"]

    def _get_related_objects(self, obj, field):
        if not obj.base_objects:
            return "-"
        objects = Counter(
            [str(getattr(base_object, field)) for base_object in obj.base_objects.all()]
        )
        return "<br>".join(
            ["{}: {}".format(name, count) for name, count in objects.most_common()]
        )

    @mark_safe
    def get_services(self, obj):
        return self._get_related_objects(obj, "service_env")

    get_services.short_description = _("services")

    @mark_safe
    def get_configuration_path(self, obj):
        return self._get_related_objects(obj=obj, field="configuration_path")

    get_configuration_path.short_description = _("configuration path")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            Prefetch(
                "base_objects",
                queryset=BaseObject.objects.distinct().select_related(
                    "configuration_path",
                    "configuration_path__module",
                    "service_env",
                    "service_env__service",
                    "service_env__environment",
                ),
            )
        )
        return qs


@register(Operation)
class OperationAdmin(
    AttachmentsMixin, ServiceEnvironmentAndConfigurationPathMixin, RalphAdmin
):
    search_fields = ["title", "description", "ticket_id"]
    list_filter = [
        "type",
        ("status", StatusFilter),
        "reporter",
        "assignee",
        "created_date",
        "update_date",
        "resolved_date",
        "base_objects",
        "base_objects__service_env",
        "base_objects__configuration_path",
    ]
    list_display = [
        "title",
        "type",
        "created_date",
        "status",
        "reporter",
        "get_ticket_url",
    ]
    list_select_related = ("reporter", "type", "status")
    raw_id_fields = ["assignee", "reporter", "base_objects"]
    resource_class = resources.OperationResource
    form = OperationAdminForm

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "type",
                    "title",
                    "status",
                    "reporter",
                    "assignee",
                    "description",
                    "ticket_id",
                    "created_date",
                    "update_date",
                    "resolved_date",
                )
            },
        ),
        (_("Objects"), {"fields": ("base_objects",)}),
    )

    @mark_safe
    def get_ticket_url(self, obj):
        return '<a href="{ticket_url}" target="_blank">{ticket_id}</a>'.format(
            ticket_url=obj.ticket_url, ticket_id=obj.ticket_id
        )

    get_ticket_url.short_description = _("ticket ID")
    get_ticket_url.admin_order_field = "ticket_id"

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
        "base_objects__asset__model__manufacturer"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow to edit datetime fields for case when new entries are
        # created manually.
        self.formfield_overrides[DateTimeField] = {"widget": AdminDateTimeWidget}

    def get_changeform_initial_data(self, request):
        initial_data = super().get_changeform_initial_data(request)
        initial_data["created_date"] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        return initial_data
