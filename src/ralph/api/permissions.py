# -*- coding: utf-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperuserOrReadonly(BasePermission):
    """
    Allow only superuser to save. Every other user has readonly rights.
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.method in SAFE_METHODS
            or (request.user and request.user.is_superuser)
        )
