# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.account.models import Perm, BoundPerm
from ralph.discovery.tests.util import DeviceFactory
from ralph.ui.tests.global_utils import (
    login_as_user,
    login_as_su,
    GroupFactory,
    UserFactory,
)


class LoginRedirectTest(TestCase):
    def setUp(self):
        self.success_login_url = reverse('find_user_home')
        self.request_headers = {'HTTP_HOST': 'localhost:8000'}

    def _get_user_by_perm(self, perm):
        group = GroupFactory(
            name=perm.name,
            boundperm_set=(BoundPerm(perm=perm),)
        )
        user = UserFactory(
            is_staff=False,
            is_superuser=False,
            groups=(group,),
        )
        return user

    def check_redirection(self, hierarchy_data):
        for perm, home_url in hierarchy_data:
            user = self._get_user_by_perm(perm)
            self.client = login_as_user(user)
            response = self.client.get(
                self.success_login_url,
                follow=True,
                **self.request_headers
            )
            self.assertEqual(response.request['PATH_INFO'], home_url)

    def test_user_no_perms(self):
        """user without perms -> show 403"""
        no_access_user = UserFactory(
            is_staff=False,
            is_superuser=False,
        )
        self.client = login_as_user(no_access_user)
        response = self.client.get(
            self.success_login_url,
            follow=True,
            **self.request_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_hierarchy(self):
        """
        Because there is no installed scrooge, always show core
        user with scrooge perms -> show core
        user with core perms -> show core

        For asset perms:
        user with asset perms -> show core
        """
        test_data = [
            Perm.has_scrooge_access,
            Perm.has_assets_access,
            Perm.has_core_access,
        ]
        for perm in test_data:
            user = self._get_user_by_perm(perm)
            self.client = login_as_user(user)
            response = self.client.get(
                self.success_login_url,
                follow=True,
                **self.request_headers
            )
            if perm == Perm.has_assets_access:
                self.assertEqual(
                    response.request['PATH_INFO'],
                    reverse('asset_search', args=('dc',)),
                )
            else:
                self.assertEqual(
                    response.request['PATH_INFO'],
                    reverse('search', args=('info', '')),
                )


class DeviceViewRegressionTest(TestCase):

    def setUp(self):
        self.client = login_as_su()

    def test_model_is_empty(self):
        device = DeviceFactory()
        url = reverse(
            'search', kwargs={'device': device.id, 'details': 'info'},
        )
        self.assertEqual(device.model, None)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
