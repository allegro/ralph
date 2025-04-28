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
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
    DataCenterFactory,
    RackFactory,
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
            302,
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
