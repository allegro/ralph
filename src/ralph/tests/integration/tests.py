# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from pluggableapp import PluggableApp
from ralph.account.models import Perm
from ralph.ui.tests.global_utils import login_as_user
from ralph.ui.tests.functional import tests_search


@unittest.skipUnless(
    getattr(settings, 'INTEGRATION_TESTS', False),
    "Passed settings are not for integration tests",
)
class IntegratedLoginRedirectTest(tests_search.LoginRedirectTest):

    def test_hierarchy(self):
        """
        user with scrooge perms -> show scrooge
        user with asset perms -> show asset
        user with core perms -> show core
        """
        test_data = [
            (Perm.has_scrooge_access,
             PluggableApp.apps['ralph_pricing'].home_url),
            (Perm.has_assets_access,
             PluggableApp.apps['ralph_assets'].home_url),
            (Perm.has_core_access, '/ui/search/info/'),
        ]
        for perm, home_url in test_data:
            user = self._get_user_by_perm(perm)
            self.client = login_as_user(user)
            response = self.client.get(
                self.success_login_url,
                follow=True,
                **self.request_headers
            )
            self.assertEqual(response.request['PATH_INFO'], home_url)
