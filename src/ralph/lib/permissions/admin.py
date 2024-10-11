# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

from django import forms
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models.query import QuerySet

from ralph.lib.mixins.forms import RequestFormMixin
from ralph.lib.permissions.models import (
    PermByFieldMixin,
    PermissionsForObjectMixin
)

logger = logging.getLogger(__name__)


class PermissionPerFieldAdminMixin(object):
    def _has_access_to_field(self, field_name, request):
        """
        Check if user has access to field

        If field is regular model's field, permission to it is checked.
        Otherwise, field is fetched from admin or model (it could be
        property, method etc) and it's '_permission_field' attribute is
        checked - it should point to regular field which permissions will
        be checked. If this attribute is not defined, user has access to
        this field.
        """
        try:
            self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            perm_field = getattr(
                (
                    getattr(self, field_name, None) or
                    getattr(self.model, field_name, None)
                ),
                '_permission_field',
                None
            )
            if perm_field:
                logger.debug(
                    'Checking permission for field {} instead of {}'.format(
                        perm_field, field_name
                    )
                )
                field_name = perm_field
            else:
                # by default user has access to the field
                return True
        return self.model.has_access_to_field(
            field_name, request.user, action='view'
        )

    # TODO: required permissions for add and change
    def get_fieldsets(self, request, obj=None):
        new_fieldsets = []
        fieldsets = super().get_fieldsets(
            request, obj
        )
        if not issubclass(self.model, PermByFieldMixin):
            return fieldsets

        for fieldset in deepcopy(fieldsets):
            fields = [
                field for field in fieldset[1]['fields']
                if self._has_access_to_field(field, request)
            ]
            if not fields:
                continue
            fieldset[1]['fields'] = fields
            new_fieldsets.append(fieldset)
        return new_fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Return read only fields respects user permissions."""
        if not issubclass(self.model, PermByFieldMixin):
            return super().get_readonly_fields(request, obj)

        can_view = self.model.allowed_fields(request.user, 'view')
        can_change = self.model.allowed_fields(request.user, 'change')
        return list(
            (can_view - can_change) |
            set(super().get_readonly_fields(request, obj))
        )

    def get_form(self, request, obj=None, **kwargs):
        """Return form with fields which user have access."""
        form = super().get_form(request, obj, **kwargs)
        if not issubclass(self.model, PermByFieldMixin):
            return form

        user_allowed_fields = self.model.allowed_fields(request.user)
        forbidden_fields = set(form._meta.fields or []) - user_allowed_fields
        if forbidden_fields:
            for field in forbidden_fields:
                form.Meta.fields.remove(field)
        return form

    def get_list_display(self, request):
        """Return fields with respect to user permissions."""
        list_display = super().get_list_display(request)

        if not issubclass(self.model, PermByFieldMixin):
            return list_display

        list_display = [
            field for field in list_display
            if self._has_access_to_field(field, request)
        ]
        return list_display


class PermissionsPerObjectFormMixin(RequestFormMixin):
    def _check_foreign_keys_permissions(self):
        """
        Check if user has permission to save chosen related models
        (ex. ForeignKeys).
        """
        for field_name, field in self.fields.items():
            value = []
            if (
                isinstance(field, forms.ModelChoiceField) and
                issubclass(field.queryset.model, PermissionsForObjectMixin)
            ):
                value = self.cleaned_data.get(field_name)
                if value and not isinstance(value, (list, tuple, QuerySet)):
                    value = [value]
            if field_name in self.fields and value:
                for obj in value:
                    if not obj.has_permission_to_object(self._user):
                        self.add_error(field_name, ValidationError(
                            "You don't have permissions to select this value"
                        ))

    def clean(self):
        super().clean()
        self._check_foreign_keys_permissions()


class PermissionPerObjectAdminMixin(object):
    """
    Admin mixin cooperating with
    `ralph.lib.permissions.models.PermissionsForObjectMixin`
    """
    def _check_obj_permission(self, request, obj=None):
        """
        Returns True if user has access to object.
        """
        obj_permission = True
        if obj and isinstance(obj, PermissionsForObjectMixin):
            obj_permission = obj.has_permission_to_object(request.user)
        return obj_permission

    def has_change_permission(self, request, obj=None):
        return (
            super().has_change_permission(request, obj) and
            self._check_obj_permission(request, obj)
        )

    def has_delete_permission(self, request, obj=None):
        return (
            super().has_delete_permission(request, obj) and
            self._check_obj_permission(request, obj)
        )

    def get_queryset(self, request):
        """
        If model has object-level permissions, narrow queryset to object
        to which user has permissions.
        """
        queryset = super().get_queryset(request)
        if issubclass(self.model, PermissionsForObjectMixin):
            queryset = self.model._get_objects_for_user(request.user, queryset)
        return queryset

    def get_field_queryset(self, db, db_field, request):
        """
        For each related field (foreign key) which has object-level permissions
        narrow result to objects for which user has permissions.
        """
        queryset = super().get_field_queryset(db, db_field, request)
        related_model = db_field.remote_field.model
        if issubclass(related_model, PermissionsForObjectMixin):
            queryset = related_model._get_objects_for_user(
                request.user, queryset
            )
        return queryset


class PermissionAdminMixin(
    PermissionPerFieldAdminMixin,
    PermissionPerObjectAdminMixin
):
    pass
