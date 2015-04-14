# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from powerdns.models import Record
from tastypie.test import ResourceTestCase

from ralph.account.models import BoundPerm, Profile, Perm
from ralph.discovery.models_device import Device
from ralph.discovery.models_network import IPAddress
from ralph.discovery.tests.util import DeviceFactory, IPAddressFactory
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.tests.util import (
    DNSDomainFactory, DNSRecordFactory, DHCPEntryFactory,
)
from ralph.ui.tests.global_utils import create_user, UserTestCase


class AccessToDeploymentApiTest(TestCase):

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

    def test_deployment_resource(self):
        resource = 'deployment'
        perms = [Perm.read_deployment, ]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)


class TestVMCreation(UserTestCase):

    fixtures=['vm_creation_setup']

    is_staff = False
    is_superuser = False

    def setUp(self):
        super(TestVMCreation, self).setUp()
        self.add_perms([Perm.has_core_access])

    def test_api_should_create_vm_when_provided_correct_data(self):
        """Correctly setup the new VM"""
        rack = Device.objects.get(pk=1)
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        new_vm_data = json.loads(self.get(response['Location']).content)
        self.assertEqual(new_vm_data['rack'], rack.name)
        self.assertEqual(new_vm_data['dc'], rack.dc)

    def test_api_should_create_vm_when_role_is_null(self):
        """Correctly setup the new VM, no role provided"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role': None,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

    def test_api_should_return_400_when_venturerole_is_missing(self):
        """Missing venture_role."""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_api_should_return_404_when_nonexistent_parent_is_given(self):
        """Providing a parent machine that doesn't exist"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.3',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_api_should_return_404_when_nonexistent_network_is_given(self):
        """Providing a network that doesn't exist"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'nonexisting_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_api_should_return_404_when_nonexistent_venture_is_given(self):
        """Providing a venture that doesn't exist"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'wrong_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_api_should_return_404_when_nonexistent_role_is_given(self):
        """Providing a venturerole that doesn't exist"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'wrong_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_api_should_return_401_when_user_is_not_logged_in(self):
        response = self.client.post(  # Using client.post not self.post
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_api_should_return_401_when_user_has_no_core_access(self):
        rack = Device.objects.get(pk=1)
        self.user.profile.boundperm_set.clear()
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_api_should_return_400_when_mac_is_already_in_use(self):
        """Trying to use existing mac"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'11.11.11.11.11.11',
                'management-ip':'10.1.1.2',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_api_should_return_404_when_the_parent_has_no_rack(self):
        """Trying to use a parent without a rack"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.1.3',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_api_should_return_404_when_environment_has_no_template(self):
        """Trying to use an environment without template configuration"""
        response = self.post(
            '/api/add_vm', json.dumps({
                'mac':'82:3c:cf:94:9d:f2',
                'management-ip':'10.1.2.1',
                'network':'test_network',
                'venture':'test_venture',
                'venture-role':'test_role',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class TestChangeIPAddress(ResourceTestCase):

    def setUp(self):
        super(TestChangeIPAddress, self).setUp()
        self.user = create_user()
        self.sample_dev = DeviceFactory()
        self.sample_ip_1 = IPAddressFactory(
            address="10.0.1.1", device=self.sample_dev,
            hostname="d001.dc",
        )
        self.sample_dhcp_entry_1 = DHCPEntryFactory(
            ip="10.0.1.1",
            mac="aa:cc:bb:11:22:33",
        )
        self.sample_dns_domain = DNSDomainFactory(name='dc')
        self.sample_dns_record = DNSRecordFactory(
            name='d001.dc',
            type='A',
            content='10.0.1.1',
            domain=self.sample_dns_domain,
        )

    def _get_credentials(self):
        return self.create_apikey(self.user.username, self.user.api_key.key)

    def test_should_return_201_when_all_is_ok(self):
        response = self.api_client.post(
            reverse(
                'api_dispatch_list',
                kwargs={
                    'resource_name': 'change-ip-address',
                    'api_name': 'v0.9',
                },
            ),
            format='json',
            data={
                'current_ip_address': '10.0.1.1',
                'new_ip_address': '10.0.1.2',
            },
            authentication=self._get_credentials(),
        )
        self.assertHttpCreated(response)
        ip_address = IPAddress.objects.get(address='10.0.1.2')
        self.assertEqual(ip_address.device.id, self.sample_dev.id)
        self.assertEqual(ip_address.hostname, 'd001.dc')
        dhcp_entry = DHCPEntry.objects.get(ip='10.0.1.2')
        self.assertEqual(dhcp_entry.mac, 'AACCBB112233')
        dns_a_record = Record.objects.get(name='d001.dc', type='A')
        self.assertEqual(dns_a_record.content, '10.0.1.2')
        dns_ptr_record = Record.objects.get(
            name='2.1.0.10.in-addr.arpa', type='PTR',
        )
        self.assertEqual(dns_ptr_record.content, 'd001.dc')

    def test_should_return_401_when_no_credentials_were_provided(self):
        response = self.api_client.post(
            reverse(
                'api_dispatch_list',
                kwargs={
                    'resource_name': 'change-ip-address',
                    'api_name': 'v0.9',
                },
            ),
            format='json',
            data={},
        )
        self.assertHttpUnauthorized(response)

    def test_should_return_400_when_improper_input_was_given(self):
        response = self.api_client.post(
            reverse(
                'api_dispatch_list',
                kwargs={
                    'resource_name': 'change-ip-address',
                    'api_name': 'v0.9',
                },
            ),
            format='json',
            data={
                'bad_key_1': '10.0.1.1',
                'bad_key_2': '10.0.1.2',
            },
            authentication=self._get_credentials(),
        )
        self.assertHttpBadRequest(response)

    def test_should_return_400_when_the_same_ip_addresses_were_given(self):
        response = self.api_client.post(
            reverse(
                'api_dispatch_list',
                kwargs={
                    'resource_name': 'change-ip-address',
                    'api_name': 'v0.9',
                },
            ),
            format='json',
            data={
                'current_ip_address': '10.0.1.1',
                'new_ip_address': '10.0.1.1',
            },
            authentication=self._get_credentials(),
        )
        self.assertHttpBadRequest(response)

    def test_should_return_400_when_nonexistent_ip_address_was_given(self):
        response = self.api_client.post(
            reverse(
                'api_dispatch_list',
                kwargs={
                    'resource_name': 'change-ip-address',
                    'api_name': 'v0.9',
                },
            ),
            format='json',
            data={
                'current_ip_address': '10.0.1.3',
                'new_ip_address': '10.0.1.2',
            },
            authentication=self._get_credentials(),
        )
        self.assertHttpBadRequest(response)
