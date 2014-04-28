# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.account.models import BoundPerm, Profile, Perm
from django.core.cache import cache
from ralph.ui.tests.global_utils import create_user

from django.test import TestCase


class BusinessApiTest(TestCase):

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

    def test_venture_resource(self):
        resource = 'venture'
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

    def test_venturelight_resource(self):
        resource = 'venturelight'
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

    def test_role_resource(self):
        resource = 'role'
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

    def test_rolelight_resource(self):
        resource = 'rolelight'
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

    def test_department_resource(self):
        resource = 'department'
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

    def test_rolepropertytype_resource(self):
        resource = 'rolepropertytype'
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

    def test_rolepropertytypevalue_resource(self):
        resource = 'rolepropertytypevalue'
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

    def test_roleproperty_resource(self):
        resource = 'roleproperty'
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

    def test_rolepropertyvalue_resource(self):
        resource = 'rolepropertyvalue'
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
