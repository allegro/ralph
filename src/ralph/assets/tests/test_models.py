# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError

from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    ConfigurationModuleFactory,
    EthernetFactory
)
from ralph.networks.tests.factories import IPAddressFactory
from ralph.tests import RalphTestCase


class ConfigurationTest(RalphTestCase):
    def setUp(self):
        self.conf_module_1 = ConfigurationModuleFactory()
        self.conf_module_2 = ConfigurationModuleFactory(parent=self.conf_module_1)
        self.conf_module_3 = ConfigurationModuleFactory(parent=self.conf_module_2)
        self.conf_class_1 = ConfigurationClassFactory(module=self.conf_module_3)

    def test_update_module_children_path(self):
        self.conf_module_3.name = "updated_name"
        self.conf_module_3.save()

        self.conf_class_1.refresh_from_db()
        self.assertTrue(
            self.conf_class_1.path.startswith("updated_name"),
        )

    def test_update_class_path_update(self):
        self.conf_class_1.class_name = "updated_name"
        self.conf_class_1.save()
        self.conf_class_1.refresh_from_db()
        self.assertTrue(self.conf_class_1.path.endswith("updated_name"))


class EthernetTest(RalphTestCase):
    def setUp(self):
        self.ip1 = IPAddressFactory()
        self.eth1 = EthernetFactory()

    def test_clear_mac_address_without_ip_should_pass(self):
        self.eth1.mac = None
        self.eth1.clean()
        self.eth1.save()

    def test_clear_mac_address_with_ip_without_dhcp_exposition_should_pass(self):  # noqa
        self.ip1.ethernet.mac = None
        self.ip1.ethernet.clean()
        self.ip1.ethernet.save()

    def test_clear_mac_address_with_ip_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip1.dhcp_expose = True
        self.ip1.save()
        self.ip1.ethernet.mac = None
        with self.assertRaises(
            ValidationError, msg="MAC cannot be empty if record is exposed in DHCP"
        ):
            self.ip1.ethernet.clean()

    def test_change_mac_address_with_ip_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip1.dhcp_expose = True
        self.ip1.save()
        self.ip1.ethernet.mac = "11:12:13:14:15:16"
        with self.assertRaises(
            ValidationError, msg="Cannot change MAC when exposing in DHCP"
        ):
            self.ip1.ethernet.clean()
