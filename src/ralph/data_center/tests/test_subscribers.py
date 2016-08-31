# -*- coding: utf-8 -*-

from copy import deepcopy

from django.test import TestCase

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
        pass

    def test_invalid_ip_address(self):
        pass

    def test_invalid_port(self):
        pass

    def test_missing_protocol(self):
        pass

    def test_missing_service_uid(self):
        pass

    def test_missing_environment(self):
        pass

    def test_if_errors_aggregate(self):
        pass


class HandleCreateVIPEventTestCase(TestCase):

    def test_create_when_vip_already_exists(self):
        pass

    def test_create_when_service_env_does_not_exist(self):
        pass

    def test_create_with_valid_event_data(self):
        pass

    def test_create_with_invalid_event_data(self):
        pass
