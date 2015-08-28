# -*- coding: utf-8 -*-
"""
Django Rest Framework Mixins to use with permissions per field and per object.
"""
from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.filters import BaseFilterBackend

from ralph.lib.permissions import PermByFieldMixin, PermissionsForObjectMixin


class PermissionsForObjectFilter(BaseFilterBackend):
    """
    Filter queryset for objects for which user has permissions (only if
    model subclasses `PermissionsForObjectMixin`).
    """
    def filter_queryset(self, request, queryset, view):
        model_cls = queryset.model
        if issubclass(model_cls, PermissionsForObjectMixin):
            queryset = model_cls._get_objects_for_user(request.user, queryset)
        return queryset


class ObjectPermissionsMixin(object):
    """
    Validate user permissions to single object if it is instance of
    `PermissionsForObjectMixin`.

    This class should be use as a mixin to
    `rest_framework.permissions.BasePermission` subclasses.
    """
    def has_object_permission(self, request, view, obj):
        result = super().has_object_permission(request, view, obj)
        if isinstance(obj, PermissionsForObjectMixin):
            result &= obj.has_permission_to_object(request.user)
        return result


class PermissionsPerFieldSerializerMixin(object):
    """
    Apply permission validation on field level.

    This class should be used as a mixin to
    `rest_framework.serializers.BaseSerializer` subclasses.
    """
    def get_field_names(self, declared_fields, model_info):
        """
        Remove fields for which user doesn't have access.

        Fields declared in serializer which aren't related from model are
        always passed here (for any user) - it's `declared_fields` in
        DRF nomenclature.
        """
        result = list(super().get_field_names(declared_fields, model_info))
        model = self.Meta.model
        permissioned_fields = set(
            list(model_info.fields.keys()) +
            list(model_info.forward_relations.keys())
        ) & set(result)
        if issubclass(model, PermByFieldMixin):
            user = self.context['request'].user
            view_fields = model.allowed_fields(user, action='view')
            for field_name in permissioned_fields - view_fields:
                result.remove(field_name)
        return result

    def _get_read_only_fields(self):
        """
        Return model read only fields for current user.
        """
        read_only_fields = set()
        model = getattr(self.Meta, 'model')
        if issubclass(model, PermByFieldMixin):
            user = self.context['request'].user
            change_fields = model.allowed_fields(user, action='change')
            view_fields = model.allowed_fields(user, action='view')
            read_only_fields = view_fields - change_fields
        return read_only_fields

    def get_extra_kwargs(self):
        """
        Apply read_only=True on (model) fields which should be read only for
        current user.

        It's applied in extra_kwargs for each field to not touch other DRF
        mechanisms.
        """
        extra_kwargs = super().get_extra_kwargs()
        for field_name in self._get_read_only_fields():
            extra_kwargs.setdefault(field_name, {})['read_only'] = True
        return extra_kwargs

    def run_validation(self, data=empty):
        """
        Perform additional check to see if readonly data is not being updated.
        Raise `rest_framework.exceptions.ValidationError` if true.
        """
        result = super().run_validation(data)
        readonly_fields = self._get_read_only_fields()
        errors = OrderedDict()
        for field in readonly_fields:
            if field in data:
                errors[field] = _('You cannot update readonly field.')
        if errors:
            raise ValidationError(errors)
        return result


class RelatedObjectsPermissionsSerializerMixin(object):
    """
    Apply permission validation on object level for related fields
    (ex. foreign keys or many to many fields).

    This class should be used as a mixin to
    `rest_framework.serializers.BaseSerializer` subclasses.
    """
    def build_relational_field(self, field_name, relation_info):
        """
        Overwrite related field queryset to objects for which current user has
        permissions.
        """
        field_class, field_kwargs = super().build_relational_field(
            field_name, relation_info
        )
        queryset = field_kwargs.get('queryset')
        if queryset and issubclass(queryset.model, PermissionsForObjectMixin):
            queryset = queryset.model._get_objects_for_user(
                self.context['request'].user, queryset
            )
            field_kwargs['queryset'] = queryset
        return field_class, field_kwargs
