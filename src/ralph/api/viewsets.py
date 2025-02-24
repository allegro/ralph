# -*- coding: utf-8 -*-
import inspect

from django.contrib.admin import SimpleListFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, relations, viewsets

from ralph.admin.sites import ralph_site
from ralph.api.filters import (
    AdditionalDjangoFilterBackend,
    ExtendedFiltersBackend,
    ImportedIdFilterBackend,
    LookupFilterBackend,
    PolymorphicDescendantsFilterBackend,
    TagsFilterBackend
)
from ralph.api.serializers import RalphAPISaveSerializer, ReversedChoiceField
from ralph.api.utils import QuerysetRelatedMixin
from ralph.lib.custom_fields.api import CustomFieldsFilterBackend
from ralph.lib.permissions.api import (
    PermissionsForObjectFilter,
    RalphPermission
)


class AdminSearchFieldsMixin(object):
    """
    Default `filter_fields` ViewSet are search and filter fields from model's
    related admin site.
    """

    _skip_admin_search_fields = False
    _skip_admin_list_filter = False
    filter_backends = [DjangoFilterBackend]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_admin_search_fields()

    def _set_admin_search_fields(self):
        admin_site = ralph_site._registry.get(self.queryset.model)
        filter_fields = list(getattr(self, "filter_fields", None) or [])
        exclude_fields = getattr(self, "exclude_filter_fields", [])
        if admin_site and not self._skip_admin_search_fields:
            filter_fields.extend(admin_site.search_fields or [])
        if admin_site and not self._skip_admin_list_filter:
            for f in admin_site.list_filter or []:
                if isinstance(f, (tuple, list)):
                    f_name = f[0]
                else:
                    f_name = f
                if f_name in exclude_fields:
                    continue
                if inspect.isclass(f) and issubclass(f, SimpleListFilter):
                    if not hasattr(f, "field"):
                        continue
                    f_name = f.parameter_name
                filter_fields.append(f_name)
        setattr(self, "filter_fields", filter_fields)


class RalphAPIViewSetMixin(QuerysetRelatedMixin, AdminSearchFieldsMixin):
    """
    Ralph API default viewset. Provides object-level permissions checking and
    model permissions checking (using Django-admin permissions).
    """

    filter_backends = AdminSearchFieldsMixin.filter_backends + [
        PermissionsForObjectFilter,
        filters.OrderingFilter,
        ExtendedFiltersBackend,
        LookupFilterBackend,
        PolymorphicDescendantsFilterBackend,
        TagsFilterBackend,
        ImportedIdFilterBackend,
        AdditionalDjangoFilterBackend,
        CustomFieldsFilterBackend,
    ]
    permission_classes = [RalphPermission]
    save_serializer_class = None
    # define dict of extended filters by single field name (usefull for
    # polymorphic models)
    # example:
    # extended_filter_fields = {
    #    'name': ['asset__hostname', 'service_environment__name', 'ip__address']
    # }
    extended_filter_fields = None

    def __init__(self, *args, **kwargs):
        if self.extended_filter_fields is None:
            self.extended_filter_fields = {}
        super().__init__(*args, **kwargs)
        # check if required permissions and filters classes are present
        if RalphPermission not in self.permission_classes:
            raise AttributeError("RalphPermission missing in permission_classes")
        if PermissionsForObjectFilter not in self.filter_backends:
            raise AttributeError(
                "PermissionsForObjectFilter missing in filter_backends"
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
                "{}SaveSerializer".format(Meta.model.__name__),
                (RalphAPISaveSerializer,),
                {
                    "Meta": Meta,
                    "serializer_choice_field": ReversedChoiceField,
                    "serializer_related_field": relations.PrimaryKeyRelatedField,
                },
            )
        return base_serializer


_viewsets_registry = {}


class RalphAPIViewSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs["_viewsets_registry"] = _viewsets_registry
        new_cls = super().__new__(cls, name, bases, attrs)
        queryset = getattr(new_cls, "queryset", None)
        if queryset is not None:  # don't evaluate queryset
            _viewsets_registry[queryset.model] = new_cls
        # filter_class should not be overwrited for RalphViewSet
        # use dedicated filter backend if you have specific needs
        if "filter_class" in attrs:
            raise TypeError("Cannot define filter_class for RalphAPIViewSet")
        return new_cls


class RalphAPIViewSet(
    RalphAPIViewSetMixin, viewsets.ModelViewSet, metaclass=RalphAPIViewSetMetaclass
):
    pass


class RalphReadOnlyAPIViewSet(
    RalphAPIViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
    metaclass=RalphAPIViewSetMetaclass,
):
    pass
