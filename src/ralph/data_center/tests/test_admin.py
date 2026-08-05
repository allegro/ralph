from unittest import mock

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.db import connection, transaction
from django.test import override_settings, RequestFactory, TransactionTestCase
from django.urls import reverse

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import ServiceEnvironmentFactory, ServiceFactory
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus, Rack
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
    DataCenterFactory,
    RackFactory,
    RackModuleFactory,
    ServerRoomFactory,
)
from ralph.lib.custom_fields.models import (
    CustomField,
    CustomFieldTypes,
    CustomFieldValue,
)


# TransactionTestCase has to be used here, since request to admin is wrapped
# in transaction (to test publishing dc host update data to hermes)
class DataCenterAssetAdminTest(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.factory = RequestFactory()
        self.dca = DataCenterAssetFactory(
            hostname="ralph1.allegro.pl", rack=RackFactory(), position=1
        )
        self.custom_fields_inline_prefix = (
            "custom_fields-customfieldvalue-content_type-object_id-"  # noqa
        )
        self.custom_field_str = CustomField.objects.create(
            name="test_str", type=CustomFieldTypes.STRING, default_value="xyz"
        )
        self.custom_field_choices = CustomField.objects.create(
            name="test_choice",
            type=CustomFieldTypes.CHOICE,
            choices="qwerty|asdfgh|zxcvbn",
            default_value="zxcvbn",
            use_as_configuration_variable=True,
        )

    def _update_dca_get_response(self, dca_data=None, inline_data=None):
        data = {
            "id": self.dca.id,
            "sn": self.dca.sn,
            "barcode": self.dca.barcode,
            "hostname": self.dca.hostname,
            "model": self.dca.model_id,
            "orientation": self.dca.orientation,
            "rack": self.dca.rack.pk,
            "position": self.dca.position,
            "service_env": self.dca.service_env_id,
            "status": self.dca.status,
            "depreciation_rate": self.dca.depreciation_rate,
            "property_of": self.dca.property_of.id,
        }
        data.update(dca_data or {})
        if inline_data:
            data.update(self._prepare_inline_data(inline_data))
        return self.client.post(self.dca.get_absolute_url(), data)

    def _update_dca(self, dca_data=None, inline_data=None):
        response = self._update_dca_get_response(dca_data, inline_data)
        self.assertEqual(
            response.status_code,
            200,
            (
                repr(response.context["form"].errors)
                if response.context and "form" in response.context
                else ""
            ),
        )

    def _prepare_inline_data(self, d):
        return {
            "{}{}".format(self.custom_fields_inline_prefix, k): v
            for (k, v) in d.items()
        }

    def test_if_mail_notification_is_send_when_dca_is_updated_through_gui(self):
        old_service = ServiceFactory(name="test")
        new_service = ServiceFactory(name="prod")
        old_service.business_owners.add(UserFactory(email="test1@test.pl"))
        new_service.business_owners.add(UserFactory(email="test2@test.pl"))
        old_service_env = ServiceEnvironmentFactory(service=old_service)
        new_service_env = ServiceEnvironmentFactory(service=new_service)
        # update without triggering signals
        DataCenterAsset.objects.filter(pk=self.dca.pk).update(
            service_env=old_service_env
        )

        data_custom_fields = {
            "TOTAL_FORMS": 3,
            "INITIAL_FORMS": 0,
        }
        self._update_dca(
            dca_data={"service_env": new_service_env.id}, inline_data=data_custom_fields
        )

        self.dca.refresh_from_db()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            "Device has been assigned to Service: {} ({})".format(
                new_service, self.dca
            ),
            mail.outbox[0].subject,
        )
        self.assertCountEqual(mail.outbox[0].to, ["test1@test.pl", "test2@test.pl"])

    @override_settings(HERMES_HOST_UPDATE_TOPIC_NAME="ralph.host_update")
    @mock.patch("ralph.data_center.publishers.publish")
    def test_if_host_update_is_published_to_hermes_when_dca_is_updated_through_gui(  # noqa: E501
        self, publish_mock
    ):
        self.cfv1 = CustomFieldValue.objects.create(
            object=self.dca,
            custom_field=self.custom_field_str,
            value="sample_value",
        )
        new_service = ServiceFactory(name="service1", uid="sc-44444")
        new_service_env = ServiceEnvironmentFactory(
            service=new_service, environment__name="dev"
        )

        data_custom_fields = {
            "TOTAL_FORMS": 3,
            "INITIAL_FORMS": 1,
            "0-id": self.cfv1.id,
            "0-custom_field": self.custom_field_str.id,
            "0-value": "sample_value22",
            "1-id": "",
            "1-custom_field": self.custom_field_choices.id,
            "1-value": "qwerty",
        }
        with transaction.atomic():
            self._update_dca(
                dca_data={
                    "service_env": new_service_env.id,
                    "hostname": "my-host.mydc.net",
                },
                inline_data=data_custom_fields,
            )
            # DCA is saved twice
            self.assertGreater(len(connection.run_on_commit), 0)

        self.dca.refresh_from_db()
        publish_data = publish_mock.call_args[0][1]
        publish_data.pop("modified")
        publish_data.pop("created")
        self.assertCountEqual(
            publish_data,
            {
                "__str__": "data center asset: " + str(self.dca),
                "configuration_path": None,
                "configuration_variables": {
                    "test_choice": "qwerty",
                },
                "custom_fields": {
                    "test_str": "sample_value22",
                    "test_choice": "qwerty",
                },
                "ethernet": [],
                "hostname": "my-host.mydc.net",
                "id": self.dca.id,
                "model": str(self.dca.model),
                "ipaddresses": [],
                "object_type": "datacenterasset",
                "parent": None,
                "remarks": "",
                "service_env": {
                    "id": new_service_env.id,
                    "service": "service1",
                    "environment": "dev",
                    "service_uid": "sc-44444",
                    "ui_url": "",
                },
                "tags": [],
                "_previous_state": {"hostname": "ralph1.allegro.pl"},
                "ui_url": "",
            },
        )
        # Despite `save` is called twice, publish update data is called only
        # once
        self.assertEqual(publish_mock.call_count, 1)
        # check if on_commit callbacks are removed from current db connections
        self.assertEqual(connection.run_on_commit, [])

    def test_hostname_is_mandatory(self):
        response = self._update_dca_get_response(
            {"hostname": "", "status": DataCenterAssetStatus.used.id}
        )
        self.assertIn("hostname", response.context["form"].errors)
        self.assertTrue(DataCenterAsset.objects.get(id=self.dca.id).hostname)

    def test_metadata_can_be_updated_from_admin(self):
        self._update_dca({"metadata": '{"some-config": {"key": "value"}}'})

        self.dca.refresh_from_db()
        self.assertEqual(self.dca.metadata, {"some-config": {"key": "value"}})

    def test_metadata_is_available_in_bulk_edit(self):
        admin = DataCenterAssetAdmin(DataCenterAsset, admin_site=AdminSite())
        self.assertIn("metadata", admin.bulk_edit_list)


class DataCenterAssetAdminAssignManagementHostnameTest(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.factory = RequestFactory()

        dc = DataCenterFactory(
            management_hostname_suffix="dc1.test", management_ip_prefix="12.34"
        )
        room = ServerRoomFactory(data_center=dc)
        rack = RackFactory(name="Rack 123", server_room=room)
        self.dca = DataCenterAssetFullFactory(  # type: DataCenterAsset
            rack=rack, position=18, status=DataCenterAssetStatus.to_deploy.id
        )
        self.dca.management_hostname = None
        self.dca.management_ip = None
        self.dca.save()

    def build_request(self, dca):
        request = self.factory.post(
            reverse("admin:data_center_datacenterasset_changelist"),
            {
                "action": "assign_mgmt_hostname",
                "_selected_action": [dca.id],
            },
        )
        request.user = self.user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def test_superuser_can_assign_mgmt_hostname_and_ip(self):
        admin = DataCenterAssetAdmin(DataCenterAsset, admin_site=AdminSite())
        request = self.build_request(self.dca)
        admin.assign_mgmt_hostname(
            request, DataCenterAsset.objects.filter(pk=self.dca.id)
        )
        self.assertEqual(self.dca.management_hostname, "rack123-18u-mgmt.dc1.test")
        self.assertEqual(self.dca.management_ip, "12.34.213.218")

    def test_superuser_can_assign_mgmt_hostname_for_server_blade(self):
        admin = DataCenterAssetAdmin(DataCenterAsset, admin_site=AdminSite())
        self.dca.slot_no = 33
        # we need to have IP first before setting hostname, this can be whatever
        self.dca.management_ip = "10.15.20.25"
        self.dca.save()
        request = self.build_request(self.dca)
        admin.assign_mgmt_hostname(
            request, DataCenterAsset.objects.filter(pk=self.dca.id)
        )
        self.assertEqual(
            self.dca.management_hostname, "rack123-18u-bay33-mgmt.dc1.test"
        )
        self.assertEqual(self.dca.management_ip, "10.15.20.25")

    def test_cant_assign_mgmt_hostname_for_server_blade_if_no_ip(self):
        admin = DataCenterAssetAdmin(DataCenterAsset, admin_site=AdminSite())
        self.dca.slot_no = 33
        self.dca.save()
        request = self.build_request(self.dca)
        admin.assign_mgmt_hostname(
            request, DataCenterAsset.objects.filter(pk=self.dca.id)
        )
        self.assertEqual(self.dca.management_hostname, "")
        self.assertEqual(self.dca.management_ip, "")


class RackModuleAdminTest(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.dc = DataCenterFactory()
        self.rack_module = RackModuleFactory(data_center=self.dc)

    def test_changelist_view(self):
        url = reverse("admin:data_center_rackmodule_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.rack_module.name)

    def test_add_rack_module(self):
        url = reverse("admin:data_center_rackmodule_add")
        data = {
            "name": "New Rack Module",
            "data_center": self.dc.id,
            "description": "Test description",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        from ralph.data_center.models.physical import RackModule

        self.assertTrue(RackModule.objects.filter(name="New Rack Module").exists())

    def test_change_rack_module(self):
        url = self.rack_module.get_absolute_url()
        data = {
            "name": "Updated Module",
            "data_center": self.dc.id,
            "description": "Updated description",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.rack_module.refresh_from_db()
        self.assertEqual(self.rack_module.name, "Updated Module")
        self.assertEqual(self.rack_module.description, "Updated description")

    def test_rack_name_display(self):
        rack = RackFactory(rack_module=self.rack_module)
        url = reverse("admin:data_center_rackmodule_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, rack.name)


class CombineRacksIntoModuleTest(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.server_room = ServerRoomFactory()
        self.rack1: Rack = RackFactory(name="Rack 1", server_room=self.server_room)  # noqa
        self.rack2: Rack = RackFactory(name="Rack 2", server_room=self.server_room)  # noqa
        self.rack3: Rack = RackFactory(name="Rack 3", server_room=self.server_room)  # noqa

    def _perform_action(self, racks):
        url = reverse("admin:data_center_rack_changelist")
        data = {
            "action": "combine",
            "_selected_action": [rack.pk for rack in racks],
        }
        return self.client.post(url, data, follow=True)

    def test_combine_racks_creates_module(self):
        from ralph.data_center.models.physical import RackModule

        response = self._perform_action([self.rack1, self.rack2, self.rack3])
        self.assertEqual(response.status_code, 200)
        module = RackModule.objects.get()
        self.assertEqual(module.name, "Module 1 / 2 / 3")
        self.assertEqual(module.data_center, self.server_room.data_center)
        self.rack1.refresh_from_db()
        self.rack2.refresh_from_db()
        self.rack3.refresh_from_db()
        self.assertEqual(self.rack1.rack_module, module)
        self.assertEqual(self.rack2.rack_module, module)
        self.assertEqual(self.rack3.rack_module, module)

    def test_combine_racks_requires_at_least_two(self):
        from ralph.data_center.models.physical import RackModule

        response = self._perform_action([self.rack1])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select at least 2 racks")
        self.assertEqual(RackModule.objects.count(), 0)

    def test_combine_racks_fails_if_already_in_module(self):
        from ralph.data_center.models.physical import RackModule

        existing_module = RackModuleFactory(data_center=self.server_room.data_center)
        self.rack1.rack_module = existing_module
        self.rack1.save()
        response = self._perform_action([self.rack1, self.rack2])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already part of a module")
        # No new module created
        self.assertEqual(RackModule.objects.count(), 1)

    def test_combine_racks_fails_if_different_data_centers(self):
        from ralph.data_center.models.physical import RackModule

        other_server_room = ServerRoomFactory(
            data_center=DataCenterFactory(name="Other DC")
        )
        rack_other_dc = RackFactory(name="Rack 99", server_room=other_server_room)
        response = self._perform_action([self.rack1, rack_other_dc])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "same data center")
        self.assertEqual(RackModule.objects.count(), 0)

    def test_combine_racks_name_uses_numbers_from_rack_names(self):
        from ralph.data_center.models.physical import RackModule

        rack_a = RackFactory(name="Row-A-10", server_room=self.server_room)
        rack_b = RackFactory(name="Row-B-5", server_room=self.server_room)
        self._perform_action([rack_a, rack_b])
        module = RackModule.objects.get()
        # regex extracts first number: 10 from "Row-A-10", 5 from "Row-B-5"
        self.assertEqual(module.name, "Module 10 / 5")

    def test_combine_racks_name_fallback_for_no_numbers(self):
        from ralph.data_center.models.physical import RackModule

        rack_a = RackFactory(name="Alpha", server_room=self.server_room)
        rack_b = RackFactory(name="Beta", server_room=self.server_room)
        self._perform_action([rack_a, rack_b])
        module = RackModule.objects.get()
        self.assertEqual(module.name, "Module Alpha / Beta")
