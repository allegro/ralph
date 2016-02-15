# -*- coding: utf-8 -*-
import inspect

from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from rest_framework import filters, permissions, relations, viewsets

from ralph.admin.helpers import get_field_by_relation_path
from ralph.admin.sites import ralph_site
from ralph.api.serializers import RalphAPISaveSerializer, ReversedChoiceField
from ralph.api.utils import QuerysetRelatedMixin
from ralph.data_importer.models import ImportedObjects
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
                if isinstance(f, (tuple, list)):
                    f_name = f[0]
                else:
                    f_name = f
                if inspect.isclass(f) and issubclass(f, SimpleListFilter):
                    if not hasattr(f, 'field'):
                        continue
                    f_name = f.parameter_name
                filter_fields.append(f_name)
        setattr(self, 'filter_fields', filter_fields)


class RalphAPIViewSetMixin(QuerysetRelatedMixin, AdminSearchFieldsMixin):
    """
    Ralph API default viewset. Provides object-level permissions checking and
    model permissions checking (using Django-admin permissions).
    """
    filter_backends = AdminSearchFieldsMixin.filter_backends + [
        PermissionsForObjectFilter, filters.OrderingFilter,
        filters.DjangoFilterBackend, filters.SearchFilter
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
                (RalphAPISaveSerializer,),
                {
                    'Meta': Meta,
                    'serializer_choice_field': ReversedChoiceField,
                    'serializer_related_field': relations.PrimaryKeyRelatedField
                }
            )
        return base_serializer


_viewsets_registry = {}


class RalphAPIViewSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['_viewsets_registry'] = _viewsets_registry
        new_cls = super().__new__(cls, name, bases, attrs)
        queryset = getattr(new_cls, 'queryset', None)
        if queryset is not None:  # don't evaluate queryset
            _viewsets_registry[queryset.model] = new_cls
        return new_cls


class RalphAPIViewSet(
    RalphAPIViewSetMixin,
    viewsets.ModelViewSet,
    metaclass=RalphAPIViewSetMetaclass
):
    extend_filter_fields = None
    allow_lookups = {
        models.IntegerField: {
            'lte', 'gte', 'lt', 'gt', 'exact', 'in', 'range', 'isnull'
        },
        models.CharField: {
            'startswith', 'istartswith', 'endswith', 'icontains', 'contains',
            'in', 'iendswith', 'isnull', 'regex', 'iregex'
        },
        models.DateField: {
            'year', 'month', 'day', 'week_day', 'range', 'isnull'
        },
        models.DateTimeField: {'hour', 'minute', 'second'},
        models.DecimalField: {
            'lte', 'gte', 'lt', 'gt', 'exact', 'in', 'range', 'isnull'
        }
    }

    def __init__(self, *args, **kwargs):
        if self.extend_filter_fields is None:
            self.extend_filter_fields = {}
        super().__init__(*args, **kwargs)

    def get_polymorphic_ids(self, polymorphic_models):
        ids = set()
        for model in polymorphic_models:
            filter_fields = []
            model_viewset = self._viewsets_registry.get(model)
            if model_viewset:
                filter_fields = getattr(model_viewset, 'filter_fields', [])

            if not filter_fields:
                # if not filter_fields from API viewset get fields
                # from django model admin
                filter_fields = ralph_site._registry[model].search_fields

            lookups = self.get_lookups(model, filter_fields)
            if lookups:
                ids |= set(model.objects.filter(
                    **lookups
                ).values_list('pk', flat=True))
        return ids

    def get_lookups(self, model, filter_fields=None):
        if filter_fields is None:
            filter_fields = self.filter_fields
        result = {}
        for field_name, value in self.request.query_params.items():
            model_field_name, _, lookup = field_name.rpartition('__')
            try:
                model_field = get_field_by_relation_path(
                    model, model_field_name
                )
            except FieldDoesNotExist:
                continue

            lookups = set()
            for cl in inspect.getmro(model_field.__class__):
                lookups |= self.allow_lookups.get(cl, set())

            if lookup in lookups and model_field_name in filter_fields:
                result.update({field_name: value})
        return result

    def get_queryset(self):
        queryset = super().get_queryset()
        # filter by imported object id
        imported_object_id = self.request.query_params.get(
            '_imported_object_id'
        )
        if imported_object_id:
            try:
                imported_obj = ImportedObjects.objects.get(
                    content_type=ContentType.objects.get_for_model(
                        queryset.model
                    ),
                    old_object_pk=imported_object_id,
                )
            except ImportedObjects.DoesNotExist:
                return queryset.model.objects.none()
            else:
                queryset = queryset.filter(pk=imported_obj.object_pk)
        # filter by extended filters (usefull in Polymorphic objects)
        for field, field_filters in self.extend_filter_fields.items():
            value = self.request.query_params.get(field, None)
            if value:
                q_param = models.Q()
                for field_name in field_filters:
                    q_param |= models.Q(**{field_name: value})
                queryset = queryset.filter(q_param)

        polymorphic_descendants = getattr(
            queryset.model, '_polymorphic_descendants', []
        )
        if polymorphic_descendants:
            ids = self.get_polymorphic_ids(polymorphic_descendants)
            if ids:
                queryset = queryset.filter(pk__in=list(ids))

        lookups = self.get_lookups(queryset.model)
        if lookups:
            queryset = queryset.filter(**lookups)

        return queryset
