# -*- coding: utf-8 -*-
import unittest

from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status

from ralph.accounts.ldap import manager_country_attribute_populate
from ralph.accounts.management.commands.ldap_sync import (
    _truncate,
    ldap_module_exists
)
from ralph.accounts.models import RalphUser, Region
from ralph.api.tests._base import RalphAPITestCase
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


class RalphUserAPITests(RalphAPITestCase):
    def test_get_user_list(self):
        url = reverse('ralphuser-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], RalphUser.objects.count())

    def test_get_user_details(self):
        region = Region.objects.create(name='EU')
        self.user1.regions.add(region)
        url = reverse('ralphuser-detail', args=(self.user1.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user1.username)
        self.assertEqual(response.data['first_name'], self.user1.first_name)
        self.assertEqual(response.data['last_name'], self.user1.last_name)
        self.assertEqual(response.data['regions'][0]['id'], region.id)

    def test_create_user_should_raise_method_not_allowed(self):
        url = reverse('ralphuser-list')
        data = {
            'username': 'ralph',
            'first_name': 'John',
            'last_name': 'Snow',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_patch_user(self):
        region = Region.objects.create(name='EU')
        url = reverse('ralphuser-detail', args=(self.user1.id,))
        data = {
            'first_name': 'Ralph',
            'last_name': 'Django',
            'regions': [region.id],
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, 'Ralph')
        self.assertEqual(self.user1.last_name, 'Django')
        self.assertIn(region, self.user1.regions.all())

    def test_patch_user_when_user_is_not_superuser_should_raise_forbidden(self):
        region = Region.objects.create(name='EU')
        self.client.force_authenticate(self.user2)
        url = reverse('ralphuser-detail', args=(self.user1.id,))
        data = {
            'first_name': 'Ralph',
            'last_name': 'Django',
            'regions': [region.id],
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
