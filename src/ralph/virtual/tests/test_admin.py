# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model

from ralph.assets.tests.factories import BaseObjectFactory
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    ServiceEnvironmentFactory
)
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import CloudHostFactory, VirtualServerFactory


class TestVirtualServerForm(RalphTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        self.client.login(username="root", password="password")
        self.virtual_server = VirtualServerFactory()
        self.url = self.virtual_server.get_absolute_url()

    def _add_management_data(self, data_dict):
        prefixes = (
            "custom_fields-customfieldvalue-content_type-object_id-",
            "clusters-",
        )
        postfixes = ("TOTAL_FORMS", "INITIAL_FORMS")

        for pre in prefixes:
            for post in postfixes:
                data_dict.update({"{}{}".format(pre, post): 0})
        return data_dict

    def _get_basic_form_data(self):
        data = {
            "hostname": "totally_random_new_hostname",
            "type": self.virtual_server.type.pk,
            "status": self.virtual_server.status,
            "service_env": self.virtual_server.service_env.pk,
        }
        return self._add_management_data(data)

    def test_data_center_asset_parent(self):
        form_data = self._get_basic_form_data()
        form_data["parent"] = DataCenterAssetFactory().pk
        response = self.client.post(self.url, form_data)
        self.assertEqual(
            response.status_code,
            302,
            (
                repr(response.context["form"].errors)
                if response.context and "form" in response.context
                else ""
            ),
        )

    def test_cloud_host_parent(self):
        form_data = self._get_basic_form_data()
        form_data["parent"] = CloudHostFactory().pk
        response = self.client.post(self.url, form_data)
        self.assertEqual(
            response.status_code,
            302,
            (
                repr(response.context["form"].errors)
                if response.context and "form" in response.context
                else ""
            ),
        )

    def test_invalid_hypervisor_type(self):
        form_data = self._get_basic_form_data()
        for obj in (
            BaseObjectFactory(),
            ServiceEnvironmentFactory(),
            VirtualServerFactory(),
            LicenceFactory(),
        ):
            form_data["parent"] = obj.pk
            response = self.client.post(self.url, form_data)
            self.assertTrue(response.context and response.context["errors"])
            errors = response.context["form"].errors
            self.assertEqual(response.status_code, 200, repr(errors))
            self.assertIn("parent", errors.keys())
            self.assertEqual(
                errors["parent"],
                ["Hypervisor must be one of DataCenterAsset or CloudHost"],
            )
