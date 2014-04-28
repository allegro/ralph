# -*- coding: utf-8 -*-
"""Tests for CI objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.cmdb.models_ci import CI
from ralph.cmdb.util import breadth_first_search_ci


class TestCI(TestCase):
    """Generic tests for a sample network of CIs"""

    fixtures = ['sample_cis']

    def setUp(self):
        self.server_a = CI.objects.get(uid='dd-1')
        self.server_b = CI.objects.get(uid='dd-2')
        self.cloud1 = CI.objects.get(uid='dn-1')
        self.cloud2 = CI.objects.get(uid='dn-2')
        self.cloud3 = CI.objects.get(uid='dn-3')
        self.venture2 = CI.objects.get(uid='br-2')

    def test_get_parents(self):
        """Test the get_parents() method on CI."""

        self.assertSetEqual(
            set(self.server_b.get_parents()),
            {self.cloud1, self.cloud2},
        )

    def test_get_children(self):
        """Test the get_parents() method on CI."""

        self.assertSetEqual(
            set(self.venture2.get_children()),
            {self.cloud2, self.cloud3},
        )

    def test_search(self):
        """Test the search utility."""

        def is_venture2(ci):
            return ci.uid == 'br-2'

        self.assertEqual(
            breadth_first_search_ci(self.server_b, is_venture2),
            (self.venture2, True)
        )

        self.assertEqual(
            breadth_first_search_ci(self.server_a, is_venture2),
            (None, None)
        )
