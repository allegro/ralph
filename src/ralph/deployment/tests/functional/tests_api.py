# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from ralph.account.models import BoundPerm, Profile, Perm
from ralph.discovery.models_device import Device
from ralph.business.models import DataCenter
from django.core.cache import cache
from django.test import TestCase
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

    def test_correct(self): 
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


    def test_correct_null_role(self): 
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

    def test_missing_data(self):
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

    def test_nonexistent_machine(self):
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

    def test_nonexistent_network(self): 
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

    def test_nonexistent_venture(self): 
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

    def test_nonexistent_role(self): 
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

    def test_unauthorized(self):
        """Only authorized users."""
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

    def test_existing_mac(self):
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

    def test_rackless_parent(self): 
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


    def test_wrong_environment(self): 
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
