# -*- coding: utf-8 -*-
import unittest

from django.test import TestCase

from ralph.accounts.ldap import manager_country_attribute_populate
from ralph.accounts.management.commands.ldap_sync import (
    _truncate,
    ldap_module_exists
)
from ralph.tests import factories

NO_LDAP_MODULE = not ldap_module_exists


@unittest.skipIf(NO_LDAP_MODULE, "'ldap' module is not installed")
class LdapSyncTest(TestCase):

    def test_long_surname_is_truncated(self):
        too_long_surname = 'this-is-to-long-surname-so-it-should-be-truncated'
        ldap_dict = {'sn': [too_long_surname]}
        default_django_surname_length = 30
        _truncate('sn', 'last_name', ldap_dict)
        self.assertEqual(
            ldap_dict['sn'],
            [too_long_surname[:default_django_surname_length]]
        )

    def test_short_surname_stays_unmodified(self):
        short_surname = 'short-surname'
        ldap_dict = {'sn': [short_surname]}
        _truncate('sn', 'last_name', ldap_dict)
        self.assertEqual(ldap_dict['sn'], [short_surname])

    def test_truncate_works_when_no_sn(self):
        ldap_dict = {}
        _truncate('sn', 'last_name', ldap_dict)


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
        user = factories.UserFactory()
        faked_ldap_user = self._get_mocked_ldap_user({
            ldap_attr: ['XXX']
        })
        with self.settings(AUTH_LDAP_USER_ATTR_MAP=override_settings):
            manager_country_attribute_populate(
                None, user, faked_ldap_user
            )
            self.assertEqual(user.country, None)

    def test_manager_country_attribute_populate_unicode_in_manager(self):
        ldap_attr = 'manager'
        override_settings = {'manager': ldap_attr}
        manager_names = [str('Żółcień'), str('John Smith')]
        user = factories.UserFactory()

        for manager_name in manager_names:
            faked_ldap_user = self._get_mocked_ldap_user({
                ldap_attr: ['CN={},OU=XXX,DC=group'.format(manager_name)]
            })

            with self.settings(AUTH_LDAP_USER_ATTR_MAP=override_settings):
                manager_country_attribute_populate(
                    None, user, faked_ldap_user
                )
            self.assertEqual(user.manager, manager_name)
            self.assertTrue(isinstance(user.manager, str))
