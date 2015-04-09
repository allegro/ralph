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
from ralph.account.ldap import manager_country_attribute_populate


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


@unittest.skipIf(NO_LDAP_MODULE, "'ldap' module is not installed")
class LdapPopulateTest(TestCase):

    def _get_mocked_ldap_user(self, attrs):
        class MockedLdapUser(object):
            @property
            def attrs(self):
                return attrs
        return MockedLdapUser()

    def test_manager_country_attribute_populate_country(self):
        ldap_attr = 'c'
        override_settings = {'country': ldap_attr}
        user = utils.UserFactory()
        user_profile = user.get_profile()
        faked_ldap_user = self._get_mocked_ldap_user({
            ldap_attr: ['XXX']
        })
        with self.settings(AUTH_LDAP_PROFILE_ATTR_MAP=override_settings):
            manager_country_attribute_populate(
                None, user_profile, faked_ldap_user
            )
            self.assertEqual(user_profile.country, None)

    def test_manager_country_attribute_populate_unicode_in_manager(self):
        ldap_attr = 'manager'
        override_settings = {'manager': ldap_attr}
        manager_names = [unicode('Żółcień'), str('John Smith')]
        user = utils.UserFactory()
        user_profile = user.get_profile()

        for manager_name in manager_names:
            faked_ldap_user = self._get_mocked_ldap_user({
                ldap_attr: ['CN={},OU=XXX,DC=group'.format(manager_name)]
            })

            with self.settings(AUTH_LDAP_PROFILE_ATTR_MAP=override_settings):
                manager_country_attribute_populate(
                    None, user_profile, faked_ldap_user
                )
            self.assertEqual(user_profile.manager, manager_name)
            self.assertTrue(isinstance(user_profile.manager, unicode))
