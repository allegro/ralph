# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList, SEARCH_VAR

SEARCH_SCOPE_VAR = "search-scope"
BULK_EDIT_VAR = "bulk_edit"
BULK_EDIT_VAR_IDS = "id"
IGNORED_FIELDS = (BULK_EDIT_VAR, BULK_EDIT_VAR_IDS, SEARCH_SCOPE_VAR)


class RalphChangeList(ChangeList):
    def __init__(self, request, *args, **kwargs):
        self.bulk_edit = request.GET.get(BULK_EDIT_VAR, False)
        super().__init__(request, *args, **kwargs)

    def get_filters_params(self, params=None):
        result = super().get_filters_params(params)
        for field in IGNORED_FIELDS:
            if field in result:
                del result[field]
        return {key: value for key, value in result.items() if value != ""}

    @property
    def any_filters(self):
        return self.get_filters_params() or self.params.get(SEARCH_VAR)

    def get_ordering_from_related_model_admin(self, prefix, field_name):
        """
        Get ordering from related model admin.
        """
        admin_site = self.model_admin.admin_site
        field = getattr(self.model, field_name, None)
        fields = [prefix + field_name]
        if not field:
            return fields
        try:
            model_admin = admin_site._registry[field.field.remote_field.model]
        except (AttributeError, KeyError):
            pass
        else:
            if all([model_admin, model_admin.ordering]):
                fields = [
                    "{}{}__{}".format(prefix, field_name, order.lstrip("-"))
                    for order in model_admin.ordering
                ]
        return fields

    def get_ordering(self, request, queryset):
        """
        Extends ordering list by list fetching from related model admin.
        """
        old_ordering = super().get_ordering(request, queryset)
        ordering = []
        for field_order in old_ordering:
            _, prefix, field = field_order.rpartition("-")
            ordering.extend(self.get_ordering_from_related_model_admin(prefix, field))
        return ordering

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if self.is_popup:
            # For popup window we limit display of records to the same as
            # we have in the autocomplete widget.
            autocomplete_queryset = getattr(
                self.model, "get_autocomplete_queryset", None
            )
            if autocomplete_queryset:
                autocomplete_queryset = autocomplete_queryset()
                # #2248 - cannot combine unique (distinct) and non-unique query
                # if one of the queries is distinct, make sure all are distinct
                if queryset.query.distinct and not autocomplete_queryset.query.distinct:
                    autocomplete_queryset = autocomplete_queryset.distinct()
                if not queryset.query.distinct and autocomplete_queryset.query.distinct:
                    queryset = queryset.distinct()
                queryset = queryset & autocomplete_queryset
        return queryset
