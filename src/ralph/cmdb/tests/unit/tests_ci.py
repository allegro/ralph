# -*- coding: utf-8 -*-
"""Tests for CI objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.cmdb.models_ci import CI, CI_STATE_TYPES
from ralph.cmdb.util import breadth_first_search_ci, walk, collect


class TestCI(TestCase):
    """Generic tests for a sample network of CIs"""

    fixtures = ['sample_cis']

    def setUp(self):
        self.server_a = CI.objects.get(uid='dd-1')
        self.server_b = CI.objects.get(uid='dd-2')
        self.server_c = CI.objects.get(uid='dd-3')
        self.cloud1 = CI.objects.get(uid='dn-1')
        self.cloud2 = CI.objects.get(uid='dn-2')
        self.cloud3 = CI.objects.get(uid='dn-3')
        self.venture1 = CI.objects.get(uid='br-1')
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

    def test_walk(self):
        """Test the walk utility."""

        def activate(ci):
            if ci.state == CI_STATE_TYPES.ACTIVE.id:
                raise AssertionError(
                    'The function applied twice on the same CI during the walk'
                )
            ci.state = CI_STATE_TYPES.ACTIVE.id
            ci.save()

        walk(self.venture1, activate, up=False)
        for ci in [
            self.venture1,
            self.cloud1,
            self.cloud2,
            self.server_a,
            self.server_b,
        ]:
            ci = CI.objects.get(pk=ci.id)
            self.assertEqual(ci.state, CI_STATE_TYPES.ACTIVE.id)
        for ci in [
            self.venture2,
            self.cloud3,
            self.server_c,
        ]:
            ci = CI.objects.get(pk=ci.id)
            self.assertEqual(ci.state, CI_STATE_TYPES.INACTIVE.id)

    def test_collect(self):
        """Test the 'collect' utility"""

        def get_name(ci):
            return [ci.name]
        names = set(collect(self.venture1, get_name, up=False))
        self.assertSetEqual(names, {
            'venture1',
            'cloud1',
            'cloud2',
            'a.example.com',
            'b.example.com'
        })


