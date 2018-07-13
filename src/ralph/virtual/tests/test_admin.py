# -*- coding: utf-8 -*-
import json

from django.core.exceptions import ValidationError

from ralph.admin.sites import ralph_site
from ralph.assets.models.base import BaseObject
from ralph.assets.tests.factories import BaseObjectFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    ServiceEnvironmentFactory
)
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests import RalphTestCase
from ralph.virtual.admin import VirtualServerAdmin, VirtualServerForm
from ralph.virtual.models import VirtualServer
from ralph.virtual.tests.factories import CloudHostFactory, VirtualServerFactory


class MockAdmin:
    def has_perm(self, perm):
        return True


class MockRequest:
    pass


class TestVirtualServerForm(RalphTestCase):
    
    def setUp(self):
        self.request = MockRequest()
        self.request.user = MockAdmin()
        self.admin = VirtualServerAdmin(VirtualServer, ralph_site)

    def _get_basic_form_data(self):
        virtual_server = VirtualServerFactory()
        return {
            'hostname': 'totally_random_new_hostname',
            'type': virtual_server.type.pk,
            'status': virtual_server.status,
            'service_env': virtual_server.service_env,
        }

    def test_data_center_asset_parent(self):
        form_data = self._get_basic_form_data()
        form_data['parent'] = DataCenterAssetFactory().pk
        form = self.admin.get_form(self.request)(data=form_data)
        form.full_clean()
        self.assertTrue(form.is_valid())

    def test_cloud_host_parent(self):
        form_data = self._get_basic_form_data()
        form_data['parent'] = CloudHostFactory().pk
        form = self.admin.get_form(self.request)(data=form_data)
        form.full_clean()
        self.assertTrue(form.is_valid())

    def test_invalid_hypervisor_type(self):
        form_data = self._get_basic_form_data()
        for obj in (
            BaseObjectFactory(),
            ServiceEnvironmentFactory(),
            VirtualServerFactory(),
            LicenceFactory()
            ):
            form_data['parent'] = obj.pk
            form = self.admin.get_form(self.request)(data=form_data)
            form.full_clean()
            self.assertFalse(form.is_valid())
            errors = json.loads(form.errors.as_json())
            self.assertEquals(len(errors.keys()), 1)
            self.assertIn('parent', errors.keys())
            self.assertEquals(errors['parent'][0]['message'], form.HYPERVISOR_TYPE_ERR_MSG)

    def test_validate_parent_type(self):
        form_data = self._get_basic_form_data()
        form = self.admin.get_form(self.request)(data=form_data)
        for obj in (
            BaseObjectFactory(),
            ServiceEnvironmentFactory(),
            VirtualServerFactory(),
            LicenceFactory()
            ):
            self.assertRaises(ValidationError, form._validate_parent_type, value=obj)
