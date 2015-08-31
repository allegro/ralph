# -*- coding: utf-8 -*-
from rest_framework.compat import get_model_name
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated
from rest_framework.permissions import BasePermission, SAFE_METHODS

from ralph.lib.permissions.api import ObjectPermissionsMixin

ADD_PERM = ['%(app_label)s.add_%(model_name)s']
CHANGE_PERM = ['%(app_label)s.change_%(model_name)s']
DELETE_PERM = ['%(app_label)s.delete_%(model_name)s']
# user could have any of add, change, delete permissions to view model
VIEW_PERM = ADD_PERM + CHANGE_PERM + DELETE_PERM


def is_staff(user):
    """
    Check if user is staff (he's staff if he has is_staff OR is_superuser flag)
    """
    return user.is_staff or user.is_superuser


class IsAuthenticated(DRFIsAuthenticated):
    """
    Extends default DRF IsAuthenticated permission and additionally check if
    user is staff.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_staff(request.user)


class IsSuperuserOrReadonly(BasePermission):
    """
    Allow only superuser to save. Every other user has readonly rights.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.method in SAFE_METHODS or
            (
                request.user and
                request.user.is_superuser
            )
        )


class RalphPermission(ObjectPermissionsMixin, IsAuthenticated):
    """
    Ralph API Permissions.

    Performed checks:
        * user has access to object (through `ObjectPermissionsMixin`)
        * user is properly authenticated (through `IsAuthenticated`)
        * user has proper Django admin permissions (add_*, change_*, delete_*)
          for model he requested
    """

    perms_map = {
        'GET': VIEW_PERM,
        'OPTIONS': VIEW_PERM,
        'HEAD': VIEW_PERM,
        'POST': ADD_PERM,
        'PUT': CHANGE_PERM,
        'PATCH': CHANGE_PERM,
        'DELETE': DELETE_PERM,
    }

    def get_required_permissions(self, method, model_cls):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': get_model_name(model_cls)
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def _check_model_permissions(self, request, view):
        """
        Check if user has permissions to model assigned to view based on Django
        admin permissions. If view doesn't have model (queryset) assigned,
        permission is granted here.
        """
        try:
            queryset = view.get_queryset()
        except (AttributeError, TypeError):
            queryset = getattr(view, 'queryset', None)

        model_perms = True
        if queryset is not None:
            perms = self.get_required_permissions(
                request.method, queryset.model
            )
            model_perms = request.user.has_any_perms(perms)
        return model_perms

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) and
            self._check_model_permissions(request, view)
        )
