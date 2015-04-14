# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase
import mock
from mock_django.signals import mock_signal_receiver

from ralph.cmdb.tests.utils import (
    CIRelationFactory,
    DeviceEnvironmentFactory,
    ServiceCatalogFactory,
)
from ralph.discovery.tests.util import DeviceFactory, IPAddressFactory
from ralph.discovery.models import DeviceType, Device, UptimeSupport
from ralph.discovery.models_history import HistoryChange
from ralph.ui.tests.global_utils import UserFactory
from ralph.util.models import fields_synced_signal, ChangeTuple
from ralph.util.tests.utils import (
    UserFactory, RolePropertyTypeFactory, RolePropertyFactory,
    VentureRoleFactory,
)
from ralph_assets.models import Orientation
from ralph_assets.tests.utils.assets import DCAssetFactory, DeviceInfoFactory


class ModelsTest(TestCase):

    def test_device_create_empty(self):
        with self.assertRaises(ValueError):
            Device.create(model_name='xxx', model_type=DeviceType.unknown)

    def test_device_create_nomodel(self):
        with self.assertRaises(ValueError):
            Device.create(sn='xxx')

    def test_device_conflict(self):
        Device.create([('1', 'DEADBEEFCAFE', 0)],
                      model_name='xxx', model_type=DeviceType.rack_server)
        Device.create([('1', 'CAFEDEADBEEF', 0)],
                      model_name='xxx', model_type=DeviceType.rack_server)
        with self.assertRaises(ValueError):
            Device.create([('1', 'DEADBEEFCAFE', 0), ('2', 'CAFEDEADBEEF', 0)],
                          model_name='yyy', model_type=DeviceType.switch)

    def test_device_create_blacklist(self):
        ethernets = [
            ('1', 'DEADBEEFCAFE', 0),
            ('2', 'DEAD2CEFCAFE', 0),
        ]
        dev = Device.create(ethernets, sn='None',
                            model_name='xxx', model_type=DeviceType.unknown)

        self.assertEqual(dev.sn, None)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(macs, ['DEADBEEFCAFE'])

    def test_device_history(self):
        dev = Device.create(
            model_name='xxx',
            model_type=DeviceType.unknown,
            sn='xaxaxa',
            user='ralph',
        )
        dev.name = 'dev1'
        dev.save()
        history = HistoryChange.objects.all()
        self.assertEqual(history[0].field_name, 'id')
        self.assertEqual(history[0].new_value, '1')
        self.assertEqual(history[1].old_value, '')
        self.assertEqual(history[1].new_value, dev.name)
        self.assertEqual(history[1].new_value, 'dev1')
        dev_db = Device.objects.get(id=dev.id)
        self.assertEqual(dev_db.name, 'dev1')
        self.assertEqual(dev_db.sn, 'xaxaxa')


class DeviceSignalTest(TestCase):
    """Device should send a signal when created."""

    def setUp(self):
        self.dev = DeviceFactory(service=ServiceCatalogFactory())

    def test_signal_sent(self):
        with mock_signal_receiver(fields_synced_signal) as rec:
            old_name = self.dev.name
            author = UserFactory()
            old_service = self.dev.service
            service = ServiceCatalogFactory()
            self.dev.service = service
            self.dev.save(user=author)
            rec.assert_called_with(
                signal=mock.ANY,
                sender=self.dev,
                changes=[ChangeTuple('service', old_service, service)],
                change_author=author,
            )


class ManagementIpTests(TestCase):
    """Tests for management IP property."""

    def test_legacy(self):
        """Legacy way of setting management_ip is readable."""
        dev = DeviceFactory()
        dev.management = IPAddressFactory(is_management=True)
        self.assertEqual(dev.management, dev.management_ip)

    def test_preferred(self):
        """Preferred way of setting management_ip is readable."""
        dev = DeviceFactory()
        management = IPAddressFactory(is_management=True)
        dev.ipaddress_set.add(management)
        self.assertEqual(management, dev.management_ip)

    def test_migrate(self):
        """Resetting the management_ip should migrate the data from legacy way
        to the preferred way"""
        dev = DeviceFactory()
        dev.management = IPAddressFactory(is_management=True)
        dev.management_ip = dev.management_ip
        self.assertEqual(dev.ipaddress_set.all()[0], dev.management_ip)
        self.assertIsNone(dev.management)

    def test_set_string(self):
        """Setting the management_ip by string"""
        dev = DeviceFactory()
        dev.management_ip = '10.1.2.3'
        self.assertEqual(dev.management_ip.address, '10.1.2.3')

    def test_set_tuple(self):
        """Setting the management_ip by tuple"""
        dev = DeviceFactory()
        data = ('hostname.dc1', '10.1.2.3')
        dev.management_ip = data
        self.assertEqual(
            (dev.management_ip.hostname, dev.management_ip.address),
            data,
        )


class MockDateTime(datetime.datetime):

    @classmethod
    def now(cls):
        return datetime.datetime(2010, 10, 3, 14, 53, 21)


class UptimeSupportTest(TestCase):

    @mock.patch('ralph.discovery.models_device.datetime.datetime', MockDateTime)
    def test_uptime(self):
        class Model(UptimeSupport):
            pass
        m = Model()
        self.assertEqual(m.uptime, None)
        m.uptime = 132
        self.assertEqual(m.uptime, datetime.timedelta(seconds=132))


class ServiceEnvironments(TestCase):

    def test_getting_environments(self):
        service = ServiceCatalogFactory()
        env = DeviceEnvironmentFactory()
        self.assertEqual(len(service.get_environments()), 0)
        CIRelationFactory(parent=service, child=env)
        self.assertEqual(len(service.get_environments()), 1)


class DeviceModelTest(TestCase):

    def test_orientation_property(self):
        dev_1 = DeviceFactory(name='h101.dc')
        dev_2 = DeviceFactory(name='h101.dc')
        DCAssetFactory(
            device_info=DeviceInfoFactory(
                ralph_device_id=dev_2.id,
                orientation=Orientation.middle.id,
            ),
        )
        self.assertEqual(dev_1.orientation, '')
        self.assertEqual(dev_2.orientation, 'middle')
        with self.assertRaises(AttributeError):
            dev_2.orientation = Orientation.back.id


class DevicePropertiesTest(TestCase):

    def setUp(self):
        sample_role = VentureRoleFactory()
        RolePropertyFactory(
            symbol='my_custom_property_1',
            type=RolePropertyTypeFactory(symbol='STRING'),
            role=sample_role,
        )
        self.sample_device = DeviceFactory(
            venture=sample_role.venture, venture_role=sample_role)
        self.sample_user = UserFactory()

    def test_successful_save(self):
        self.sample_device.set_property(
            symbol='my_custom_property_1', value='Test 123',
            user=self.sample_user,
        )
        self.assertEqual(
            self.sample_device.get_property_set(),
            {'my_custom_property_1': 'Test 123'}
        )
