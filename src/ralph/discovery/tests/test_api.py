# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from django.core.cache import cache
from django.test import TestCase

from ralph.account.models import BoundPerm, Profile, Perm
from ralph.discovery.tests.util import NetworkFactory
from ralph.ui.tests.global_utils import create_user, UserFactory


class AccessToDiscoveyApiTest(TestCase):

    def setUp(self):
        self.user = create_user(
            'api_user',
            'test@mail.local',
            'password',
            is_staff=False,
            is_superuser=False,
        )
        self.api_login = {
            'format': 'json',
            'username': self.user.username,
            'api_key': self.user.api_key.key,
        }
        cache.delete("api_user_accesses")

    def get_response(self, resource):
        path = "/api/v0.9/%s/" % resource
        response = self.client.get(
            path=path,
            data=self.api_login,
            format='json',
        )
        return response

    def add_perms(self, perms):
        user_profile = Profile.objects.get(user=self.user)
        for perm in perms:
            BoundPerm(profile=user_profile, perm=perm).save()

    def test_ipaddress_resource(self):
        resource = 'ipaddress'
        perms = [Perm.read_network_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_model_resource(self):
        resource = 'model'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_device_resource(self):
        resource = 'dev'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_physicalserver_resource(self):
        resource = 'physicalserver'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_rackserver_resource(self):
        resource = 'rackserver'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_bladeserver_resource(self):
        resource = 'bladeserver'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_virtualserver_resource(self):
        resource = 'virtualserver'
        perms = [Perm.read_dc_structure, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)


class TestNetworksResource(TestCase):

    def setUp(self):
        self.user = UserFactory(
            username='api_user', email='api_user@ralph.local', is_staff=True,
            is_superuser=True,
        )
        self.user.set_password('QWEasd')
        self.user.save()
        self.net_1 = NetworkFactory(
            name='test-net-1.dc',
            address="192.168.1.0/24",
        )
        self.net_1.save()
        self.net_2 = NetworkFactory(
            name='test-net-2.dc',
            address="192.168.56.0/24",
        )
        self.net_2.save()

    def _get_networks_names(self, result):
        return [
            network['name'] for network in result['objects']
        ]

    def test_resource(self):
        path = "/api/v0.9/networks/"
        # sort by min_ip
        response = self.client.get(
            path=path,
            data={
                'format': 'json',
                'username': self.user.username,
                'api_key': self.user.api_key.key,
                'order_by': 'min_ip',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(
            self._get_networks_names(result),
            ['test-net-1.dc', 'test-net-2.dc'],
        )
        # sort by max_ip
        response = self.client.get(
            path=path,
            data={
                'format': 'json',
                'username': self.user.username,
                'api_key': self.user.api_key.key,
                'order_by': '-max_ip',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(
            self._get_networks_names(result),
            ['test-net-2.dc', 'test-net-1.dc'],
        )
        # filter by min_ip
        response = self.client.get(
            path=path,
            data={
                'format': 'json',
                'username': self.user.username,
                'api_key': self.user.api_key.key,
                'min_ip__lte': '3232235777',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(
            self._get_networks_names(result),
            ['test-net-1.dc'],
        )
