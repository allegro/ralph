# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList

SEARCH_SCOPE_VAR = 'search-scope'
BULK_EDIT_VAR = 'bulk_edit'
BULK_EDIT_VAR_IDS = 'id'
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
        return result

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
            model_admin = admin_site._registry[field.field.rel.to]
        except AttributeError:
            pass
        else:
            if all([model_admin, model_admin.ordering]):
                fields = [
                    '{}{}__{}'.format(prefix, field_name, order.lstrip('-'))
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
            _, prefix, field = field_order.rpartition('-')
            ordering.extend(
                self.get_ordering_from_related_model_admin(prefix, field)
            )
        return ordering
