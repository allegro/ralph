# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.samples.dell_idrac_data import DATA
from ralph.discovery.http import guess_family


class DiscoveryHttpTest(TestCase):

    def test_guess_family(self):
        headers = {}
        family = guess_family(headers, DATA)
        self.assertEqual(family, 'Dell')
