# -*- coding: utf-8 -*-
import inspect

from django.contrib.admin import SimpleListFilter
from rest_framework import (
    filters,
    permissions,
    relations,
    serializers,
    viewsets
)

from ralph.admin.sites import ralph_site
from ralph.api.permissions import RalphPermission
from ralph.api.serializers import ReversedChoiceField
from ralph.api.utils import QuerysetRelatedMixin
from ralph.lib.permissions.api import PermissionsForObjectFilter


class AdminSearchFieldsMixin(object):
    """
    Default `filter_fields` ViewSet are search and filter fields from model's
    related admin site.
    """
    _skip_admin_search_fields = False
    _skip_admin_list_filter = False
    filter_backends = [filters.DjangoFilterBackend]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_admin_search_fields()

    def _set_admin_search_fields(self):
        admin_site = ralph_site._registry.get(self.queryset.model)
        filter_fields = getattr(self, 'filter_fields', None) or []
        if admin_site and not self._skip_admin_search_fields:
            filter_fields.extend(admin_site.search_fields or [])
        if admin_site and not self._skip_admin_list_filter:
            for f in admin_site.list_filter or []:
                f_name = f
                if inspect.isclass(f) and issubclass(f, SimpleListFilter):
                    f_name = f.parameter_name
                filter_fields.append(f_name)
        setattr(self, 'filter_fields', filter_fields)


class RalphAPIViewSetMixin(QuerysetRelatedMixin, AdminSearchFieldsMixin):
    """
    Ralph API default viewset. Provides object-level permissions checking and
    model permissions checking (using Django-admin permissions).
    """
    filter_backends = AdminSearchFieldsMixin.filter_backends + [
        PermissionsForObjectFilter, filters.OrderingFilter
    ]
    permission_classes = [RalphPermission]
    save_serializer_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # check if required permissions and filters classes are present
        if RalphPermission not in self.permission_classes:
            raise AttributeError(
                'RalphPermission missing in permission_classes'
            )
        if PermissionsForObjectFilter not in self.filter_backends:
            raise AttributeError(
                'PermissionsForObjectFilter missing in filter_backends'
            )

    def get_serializer_class(self):
        """
        If it's not safe request (ex. POST) and there is `save_serializer_class`
        specified, return it, otherwise create default serializer with
        `PrimaryKeyRelatedField` serializer for related fields.

        If it's safe request, just return regular viewset serializer.
        """
        base_serializer = super().get_serializer_class()
        if self.request.method not in permissions.SAFE_METHODS:
            if self.save_serializer_class:
                return self.save_serializer_class

            # create default class for save (POST, PUT etc.) serialization
            # where every related field is serialized by it's primary key
            class Meta(base_serializer.Meta):
                model = self.queryset.model
                depth = 0

            return type(
                '{}SaveSerializer'.format(Meta.model.__name__),
                (serializers.ModelSerializer,),
                {
                    'Meta': Meta,
                    'serializer_choice_field': ReversedChoiceField,
                    'serializer_related_field': relations.PrimaryKeyRelatedField
                }
            )
        return base_serializer


class RalphAPIViewSet(RalphAPIViewSetMixin, viewsets.ModelViewSet):
    pass
