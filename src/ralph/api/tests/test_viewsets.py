# -*- coding: utf-8 -*-
from ralph.api.viewsets import RalphAPIViewSet
from ralph.tests import RalphTestCase


class ViewsetWithoutRalphPermission(RalphAPIViewSet):
    permission_classes = []


class ViewsetWithoutPermissionsForObjectFilter(RalphAPIViewSet):
    filter_backends = []


class TestRalphViewset(RalphTestCase):
    def test_should_raise_attributeerror_when_ralph_permission_missing(self):
        with self.assertRaises(AttributeError):
            ViewsetWithoutRalphPermission()

    def test_should_raise_attributeerror_when_permission_for_object_filter_missing(self):  # noqa
        with self.assertRaises(AttributeError):
            ViewsetWithoutPermissionsForObjectFilter()
