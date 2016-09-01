# -*- coding: utf-8 -*-

from copy import deepcopy

from django.test import TestCase

from ralph.data_center.subscribers import (
    validate_event_data,
)

EVENT_DATA = {
    "non_http": False,
    "load_balancer": "test-lb.local",
    "id": 111,
    "service": {
        "uid": "xx-123",
        "name": "test service"
    },
    "load_balancer_type": "HAPROXY",
    "port": 8000,
    "name": "ralph-test.local_8000",
    "environment": "test",
    "venture": None,
    "protocol": "TCP",
    "partition": "default",
    "ip": "10.20.30.40"
}

class ValidateEventDataTestCase(TestCase):

    def setUp(self):
        self.data = deepcopy(EVENT_DATA)

    def test_missing_name(self):
        self.data['name'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('missing name', errors)

    def test_invalid_ip_address(self):
        self.data['ip'] = '10.20.30.40.50'
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid IP address "10.20.30.40.50"', errors)

        self.data['ip'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid IP address "None"', errors)

    def test_invalid_port(self):
        self.data['port'] = 80
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid port "80"', errors)

        self.data['port'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid port "None"', errors)

    def test_missing_protocol(self):
        self.data['protocol'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('missing protocol', errors)

    def test_missing_service_uid(self):
        self.data['service']['uid'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('missing service UID', errors)

        self.data['service'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('missing service UID', errors)

    def test_missing_environment(self):
        self.data['environment'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 1)
        self.assertIn('missing environment', errors)

    def test_if_errors_aggregate(self):
        self.data['service'] = None
        self.data['environment'] = None
        errors = validate_event_data(self.data)
        self.assertEqual(len(errors), 2)
        self.assertIn('missing service UID', errors)
        self.assertIn('missing environment', errors)


class HandleCreateVIPEventTestCase(TestCase):

    def test_create_when_vip_already_exists(self):
        pass

    def test_create_when_service_env_does_not_exist(self):
        pass

    def test_create_with_valid_event_data(self):
        pass

    def test_create_with_invalid_event_data(self):
        pass


class HandleDeleteVIPEventTestCase(TestCase):

    def test_create_when_vip_already_exists(self):
        pass

    def test_create_when_service_env_does_not_exist(self):
        pass

    def test_create_with_valid_event_data(self):
        pass

    def test_create_with_invalid_event_data(self):
        pass
