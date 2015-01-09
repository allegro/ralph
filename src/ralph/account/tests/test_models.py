# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from django.conf import settings
from ralph.account.models import Region
from ralph.account.tests import utils

from ralph.discovery.tests.util import RackFactory

class ModelsTest(TestCase):

    def test_getting_default_region(self):
        region = Region.get_default_region()
        self.assertEqual(region.name, settings.DEFAULT_REGION_NAME)

    def test_getting_regions(self):
        user = utils.UserFactory()
        user_profile = user.get_profile()
        default_region = Region.objects.get(name=settings.DEFAULT_REGION_NAME)

        self.assertEqual(len(user_profile.get_regions()), 1)
        self.assertEqual(user_profile.get_regions()[0], default_region)

        nld_region = utils.RegionFactory(name='NLD')
        user_profile.region_set.add(nld_region)
        self.assertEqual(len(user_profile.get_regions()), 1)
        self.assertEqual(user_profile.get_regions()[0], nld_region)

    def test_if_region_is_granted_or_not(self):
        nld_region = utils.RegionFactory(name='NLD')
        user_profile = utils.UserFactory().get_profile()

        self.assertFalse(user_profile.is_region_granted(nld_region))
        user_profile.region_set.add(nld_region)
        self.assertTrue(user_profile.is_region_granted(nld_region))
