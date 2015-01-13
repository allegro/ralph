# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.discovery.models import IPAddress
from ralph.ui.tests.global_utils import login_as_user, UserFactory


class ScanFormTest(TestCase):

    def setUp(self):
        user = UserFactory(is_superuser=True)
        self.client = login_as_user(user)

    def test_ip_does_not_exist(self):
        """Checks the situation in which you want to scan IP address that
        does not exist in the database. The form creates and displays
        the ip address on Scan form.
        """

        ip = '127.0.0.1'
        url = reverse(
            'search', kwargs={'details': 'scan', 'address': ip},
        )

        self.assertEqual(IPAddress.objects.count(), 0)

        response = self.client.get(url, follow=True)
        self.assertContains(
            response,
            "Scanning {}".format(ip),
            status_code=200,
        )
        self.assertTrue(IPAddress.objects.filter(address=ip).exists())
