# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.samples.dell_idrac_data import DATA
from ralph.discovery.http import guess_family


class DiscoveryHttpTest(TestCase):

    def test_guess_family_dell_when_data_from_dell_server(self):
        headers = {}
        family = guess_family(headers, DATA)
        self.assertEqual(family, 'Dell')

    def test_guess_family_xen_when_data_from_xen(self):
        headers = {}
        family = guess_family(headers, """
            <html>
                <title>XenServer 6.5.0</title>
                <head>
                </head>
                <body>
                  <p/>Citrix Systems, Inc. XenServer 6.5.0
                  <p/><a href="XenCenter.iso">XenCenter CD image</a>
                  <p/><a href="XenCenterSetup.exe">XenCenter installer</a>
                </body>
            </html>"""
        )
        self.assertEqual(family, 'Xen')
