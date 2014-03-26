# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.account.models import BoundPerm, Profile, Perm
from django.core.cache import cache
from ralph.ui.tests.global_utils import create_user

from django.test import TestCase


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
