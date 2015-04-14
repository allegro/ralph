# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from ralph_assets.tests.utils.assets import AssetFactory, DeviceInfoFactory
from ralph.cmdb.tests.utils import (
    DeviceEnvironmentFactory,
    ServiceCatalogFactory,
)
from ralph.deployment import util
from ralph.deployment.models import Deployment
from ralph.deployment.tests.utils import MassDeploymentFactory, PrebootFactory
from ralph.deployment.util import (
    _change_device_ip_address,
    _change_ip_address_dhcp_entry,
    _change_ip_address_validation,
    _get_changed_ip_address_object,
    _get_connected_device,
    _get_or_create_ip_address,
    ChangeIPAddressError,
)
from ralph.discovery.models import IPAddress
from ralph.discovery.tests.util import (
    DeviceFactory,
    IPAddressFactory,
    EthernetFactory,
)
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.tests.util import DHCPEntryFactory
from ralph.ui.tests.global_utils import UserFactory
from ralph.util.tests.utils import VentureRoleFactory

class ChangeIPAddressValidationTest(TestCase):

    def test_change_ip_address_validation(self):
        self.assertRaises(
            ChangeIPAddressError,
            _change_ip_address_validation,
            "127.0.0.",
            "127.0.0.2",
        )
        self.assertRaises(
            ChangeIPAddressError,
            _change_ip_address_validation,
            "127.0.0.1",
            "127.0.0.",
        )
        self.assertRaises(
            ChangeIPAddressError,
            _change_ip_address_validation,
            "127.0.0.1",
            "127.0.0.1",
        )


class IPAddressToolsTest(TestCase):

    def setUp(self):
        self.sample_ip = IPAddressFactory(address="127.0.0.1")

    def test_get_changed_ip_address_object_success(self):
        self.assertEqual(
            _get_changed_ip_address_object("127.0.0.1").id,
            self.sample_ip.id,
        )

    def test_get_changed_ip_address_object_fail(self):
        self.assertRaises(
            ChangeIPAddressError,
            _get_changed_ip_address_object,
            "127.0.0.2",
        )

    def test_get_or_create_ip_address(self):
        self.assertEqual(
            _get_or_create_ip_address("127.0.0.1").id,
            self.sample_ip.id,
        )
        self.assertEqual(
            _get_or_create_ip_address("127.0.0.11").address,
            "127.0.0.11",
        )


class GetConnectedDeviceTest(TestCase):

    def setUp(self):
        self.sample_dev = DeviceFactory()
        self.sample_ip_1 = IPAddressFactory(
            address="127.0.0.1", device=self.sample_dev,
        )
        self.sample_ip_2 = IPAddressFactory(address="127.0.0.2")

    def test_get_connected_device_success(self):
        self.assertEqual(
            _get_connected_device(self.sample_ip_1).id,
            self.sample_dev.id,
        )

    def test_get_connected_device_errors(self):
        # IP address is not assigned to any device.
        self.assertRaises(
            ChangeIPAddressError,
            _get_connected_device,
            self.sample_ip_2,
        )


class ChangeDeviceIPAddressTest(TestCase):

    def setUp(self):
        self.sample_dev = DeviceFactory()
        self.sample_ip_1 = IPAddressFactory(
            address="10.0.0.1", device=self.sample_dev,
            hostname="dev1.dc",
        )
        self.sample_ip_2 = IPAddressFactory(
            address="10.0.0.2", hostname='dev2.dc',
        )

    def test_change_device_ip(self):
        _change_device_ip_address(
            device=self.sample_dev,
            current_ip_obj=self.sample_ip_1,
            new_ip_obj=self.sample_ip_2,
        )
        sample_ip_1 = IPAddress.objects.get(
            pk=self.sample_ip_1.id
        )
        sample_ip_2 = IPAddress.objects.get(
            pk=self.sample_ip_2.id
        )
        self.assertIsNone(sample_ip_1.device)
        self.assertIsNone(sample_ip_1.hostname)
        self.assertEqual(
            sample_ip_2.device.id,
            self.sample_dev.id,
        )
        self.assertEqual(
            sample_ip_2.hostname, 'dev1.dc',
        )


class ChangeDHCPEntiesTest(TestCase):

    def setUp(self):
        self.entry_1 = DHCPEntryFactory(
            ip="10.10.0.1",
            mac="aa:cc:bb:11:22:33",
        )
        self.entry_2 = DHCPEntryFactory(
            ip="10.10.0.2",
            mac="aa:cc:bb:11:22:44",
        )
        self.sample_ip_1 = IPAddressFactory(
            address="10.10.0.1",
        )
        self.sample_ip_2 = IPAddressFactory(
            address="10.10.0.2",
        )
        self.sample_ip_3 = IPAddressFactory(
            address="10.10.0.3",
        )

    def test_change_ip_address_dhcp_entry_success(self):
        _change_ip_address_dhcp_entry(
            self.sample_ip_1, self.sample_ip_2,
        )
        entry = DHCPEntry.objects.get(pk=self.entry_1.id)
        self.assertEqual(entry.mac, "AACCBB112233")
        self.assertEqual(entry.ip, "10.10.0.2")
        self.assertFalse(
            DHCPEntry.objects.filter(mac="AACCBB112244").exists(),
        )

    def test_change_ip_address_dhcp_entry_fail(self):
        self.assertRaises(
            ChangeIPAddressError,
            _change_ip_address_dhcp_entry,
            self.sample_ip_3,
            self.sample_ip_1,
        )


class CreateDeploymentsTest(TestCase):

    def setUp(self):
        venture_role = VentureRoleFactory()
        device_environment = DeviceEnvironmentFactory()
        service = ServiceCatalogFactory()
        self.mass_deployment = MassDeploymentFactory()
        self.user = UserFactory()
        self.data = {
            "mac": "00:00:00:00:00:00",
            "ip": "192.168.1.1",
            "hostname": "testhost.dc2",
            "preboot": PrebootFactory(),
            "venture": venture_role.venture,
            "venture_role": venture_role,
            "service": service.name,
            "device_environment": device_environment.name,
            "asset_identity": None,
        }

    def test_when_everything_works_fine(self):
        EthernetFactory(mac="000000000000")
        util.create_deployments([self.data], self.user, self.mass_deployment)

        self.assertEqual(Deployment.objects.count(), 1)

    def test_when_device_does_not_exist_and_asset_identity_is_given(self):
        device = DeviceFactory()
        device_info = DeviceInfoFactory(ralph_device_id=device.id)
        asset = AssetFactory(
            barcode="testbarcode",
            device_info=device_info,
        )
        self.data.update({"asset_identity": asset.barcode})
        util.create_deployments([self.data], self.user, self.mass_deployment)

        deployments = Deployment.objects.all()
        self.assertEqual(deployments.count(), 1)
        self.assertEqual(deployments[0].device, device)

    def test_when_device_does_not_exist_and_there_is_no_asset_identity(self):
        device = DeviceFactory()
        util._create_device = lambda x: device
        util.create_deployments([self.data], self.user, self.mass_deployment)

        deployments = Deployment.objects.all()
        self.assertEqual(deployments.count(), 1)
        self.assertEqual(deployments[0].device, device)
