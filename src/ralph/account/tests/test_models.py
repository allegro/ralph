# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from django.test import TestCase

from django.conf import settings
from ralph.account.models import Region
from ralph.account.tests import utils


try:
    from ralph.account.management.commands.ldap_sync import _truncate_surname
    NO_LDAP_MODULE = False
except ImportError:
    NO_LDAP_MODULE = True


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


@unittest.skipIf(NO_LDAP_MODULE, "'ldap' module is not installed")
class LdapSyncTest(TestCase):

    def test_long_surname_is_truncated(self):
        too_long_surname = 'this-is-to-long-surname-so-it-should-be-truncated'
        ldap_dict = {'sn': [too_long_surname]}
        default_django_surname_length = 30
        _truncate_surname(ldap_dict)
        self.assertEqual(
            ldap_dict['sn'],
            [too_long_surname[:default_django_surname_length]]
        )

    def test_short_surname_stays_unmodified(self):
        short_surname = 'short-surname'
        ldap_dict = {'sn': [short_surname]}
        _truncate_surname(ldap_dict)
        self.assertEqual(ldap_dict['sn'], [short_surname])

    def test_truncate_works_when_no_sn(self):
        ldap_dict = {}
        _truncate_surname(ldap_dict)
