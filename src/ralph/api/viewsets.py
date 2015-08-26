# -*- coding: utf-8 -*-
from rest_framework import viewsets

from ralph.api.permissions import RalphPermission
from ralph.lib.permissions.api import PermissionsForObjectFilter


class RalphAPIViewSetMixin(object):
    """
    Ralph API default viewset. Provides object-level permissions checking and
    model permissions checking (using Django-admin permissions).
    """
    filter_backends = [PermissionsForObjectFilter]
    permission_classes = [RalphPermission]

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


class RalphAPIViewSet(RalphAPIViewSetMixin, viewsets.ModelViewSet):
    pass
