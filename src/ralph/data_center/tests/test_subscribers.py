# -*- coding: utf-8 -*-

from copy import deepcopy

from django.test import TestCase

from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.data_center.models import Cluster, VIP, VIPProtocol
from ralph.data_center.subscribers import (
    handle_create_vip_event,
    handle_delete_vip_event,
    handle_update_vip_event,
    validate_vip_event_data
)
from ralph.data_center.tests.factories import (
    ClusterFactory,
    EthernetFactory,
    VIPFactory
)
from ralph.networks.models.networks import Ethernet, IPAddress
from ralph.networks.tests.factories import IPAddressFactory

EVENT_DATA = {
    "non_http": False,
    "load_balancer": "test-lb.local",
    "id": 111,
    "service": {"uid": "xx-123", "name": "test service"},
    "load_balancer_type": "HAPROXY",
    "port": 8000,
    "name": "ralph-test.local_8000",
    "environment": "test",
    "venture": None,
    "protocol": "TCP",
    "partition": "default",
    "ip": "10.20.30.40",
}


class ValidateEventDataTestCase(TestCase):
    def setUp(self):
        self.data = deepcopy(EVENT_DATA)

    def test_missing_name(self):
        self.data["name"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing name", errors)

    def test_invalid_ip_address(self):
        self.data["ip"] = "10.20.30.40.50"
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid IP address "10.20.30.40.50"', errors)

        self.data["ip"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid IP address "None"', errors)

    def test_invalid_port(self):
        self.data["port"] = 65536
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid port "65536"', errors)

        self.data["port"] = -1
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid port "-1"', errors)

        self.data["port"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid port "None"', errors)

    def test_missing_protocol(self):
        self.data["protocol"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing protocol", errors)

    def test_missing_service_uid(self):
        self.data["service"]["uid"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing service UID", errors)

        self.data["service"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing service UID", errors)

    def test_missing_environment(self):
        self.data["environment"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing environment", errors)

    def test_if_errors_aggregate(self):
        self.data["service"] = None
        self.data["environment"] = None
        errors = validate_vip_event_data(self.data)
        self.assertEqual(len(errors), 2)
        self.assertIn("missing service UID", errors)
        self.assertIn("missing environment", errors)


class HandleCreateVIPEventTestCase(TestCase):
    def setUp(self):
        self.data = deepcopy(EVENT_DATA)

    def test_create_when_vip_already_exists(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        vips = VIP.objects.all()
        self.assertEqual(vips.count(), 1)
        modified_before = vips[0].modified
        handle_create_vip_event(self.data)
        vips = VIP.objects.all()
        self.assertEqual(vips.count(), 1)
        self.assertEqual(vips[0].modified, modified_before)

    def test_create_when_service_env_does_not_exist(self):
        self.data["service"]["uid"] = "non-existing-uid"
        handle_create_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 0)

    def test_create_with_valid_event_data(self):
        service_env = ServiceEnvironmentFactory()
        self.data["service"]["uid"] = service_env.service.uid
        self.data["environment"] = service_env.environment.name
        self.assertEqual(VIP.objects.count(), 0)
        handle_create_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 1)

    def test_create_with_invalid_event_data(self):
        self.data["service"] = None
        self.assertEqual(VIP.objects.count(), 0)
        handle_create_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 0)


class HandleUpdateVIPEventTestCase(TestCase):
    def setUp(self):
        self.data = deepcopy(EVENT_DATA)

    def test_update_change_service_env(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name
        service_env = ServiceEnvironmentFactory()
        self.data["service"]["uid"] = service_env.service.uid
        self.data["environment"] = service_env.environment.name

        vips = VIP.objects.all()
        self.assertEqual(vips.count(), 1)
        handle_update_vip_event(self.data)
        vips = VIP.objects.all()
        self.assertEqual(vips.count(), 1)
        self.assertEqual(vips[0].service_env, service_env)

    def test_update_change_cluster(self):
        cluster_old = ClusterFactory(name="f5-1-fake-old")
        ethernet = EthernetFactory(base_object=cluster_old)
        vip = VIPFactory(
            ip=IPAddressFactory(ethernet=ethernet),
            parent=cluster_old,
        )
        self.data["load_balancer"] = "f5-1-fake-new"
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        self.assertEqual(VIP.objects.count(), 1)
        self.assertEqual(Cluster.objects.count(), 1)
        self.assertEqual(Ethernet.objects.count(), 1)

        handle_update_vip_event(self.data)

        vips = VIP.objects.all()
        self.assertEqual(vips.count(), 1)
        self.assertEqual(Cluster.objects.count(), 2)
        self.assertEqual(Ethernet.objects.count(), 1)
        self.assertEqual(vips[0].ip.ethernet, ethernet)
        self.assertEqual(
            Ethernet.objects.get(id=ethernet.id).base_object.last_descendant.name,
            self.data["load_balancer"],
        )


class HandleDeleteVIPEventTestCase(TestCase):
    def setUp(self):
        self.data = deepcopy(EVENT_DATA)

    def test_delete_when_ip_does_not_exist(self):
        vip = VIPFactory()
        ip = IPAddressFactory()
        self.data["ip"] = ip.address
        ip.delete()
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        self.assertEqual(VIP.objects.count(), 1)
        handle_delete_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 1)

    def test_delete_with_valid_event_data(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        self.assertEqual(VIP.objects.count(), 1)
        handle_delete_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 0)

    def test_delete_with_invalid_event_data(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        self.data["service"] = None
        self.assertEqual(VIP.objects.count(), 1)
        handle_delete_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 1)

    def test_ip_with_eth_being_deleted_when_no_longer_used(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name

        self.assertEqual(VIP.objects.count(), 1)
        self.assertEqual(IPAddress.objects.count(), 1)
        self.assertEqual(Ethernet.objects.count(), 1)
        handle_delete_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 0)
        self.assertEqual(IPAddress.objects.count(), 0)
        self.assertEqual(Ethernet.objects.count(), 0)

    def test_ip_with_eth_not_being_deleted_when_still_used_by_some_vip(self):
        vip = VIPFactory()
        self.data["ip"] = vip.ip.address
        self.data["port"] = vip.port
        self.data["protocol"] = VIPProtocol.from_id(vip.protocol).name
        vip2 = VIPFactory()
        vip2.ip = vip.ip
        vip2.save()

        self.assertEqual(VIP.objects.count(), 2)
        self.assertEqual(IPAddress.objects.count(), 2)
        self.assertEqual(Ethernet.objects.count(), 2)
        handle_delete_vip_event(self.data)
        self.assertEqual(VIP.objects.count(), 1)
        self.assertEqual(IPAddress.objects.count(), 2)
        self.assertEqual(Ethernet.objects.count(), 2)
