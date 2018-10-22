# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.accounts.models import RalphUser, Region
from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.admin.autocomplete import AutocompleteList


class AutocompleteSplitWordTest(TestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory(
            first_name='first_name_1',
            last_name='last_name_1'
        )
        UserFactory(
            first_name='first_name_2',
            last_name='last_name_2'
        )
        self.region = RegionFactory(name='pl')
        RegionFactory(name='de')

    def test_or(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = RalphUser
        result = autocomplete_list.get_query_filters(
            RalphUser.objects.all(),
            'first_name_1 last_name_1',
            ['username', 'first_name', 'last_name']
        )
        self.assertEqual(list(result), [self.user])

    def test_or_empty(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = RalphUser
        result = autocomplete_list.get_query_filters(
            RalphUser.objects.all(),
            'first_name_1 last_name_2',
            ['username', 'first_name', 'last_name']
        )
        self.assertEqual(len(result), 0)

    def test_not_or(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = Region
        result = autocomplete_list.get_query_filters(
            Region.objects.all(),
            'pl',
            ['name']
        )
        self.assertEqual(list(result), [self.region])

    def test_not_or_empty(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = Region
        result = autocomplete_list.get_query_filters(
            Region.objects.all(),
            'pl de',
            ['name']
        )
        self.assertEqual(len(result), 0)

    def test_autocomplete_endpoint_required_auth(self):
        url = reverse(
            'autocomplete-list',
            kwargs={
                'app': 'assets',
                'field': 'service_env',
                'model': 'BaseObject'
            }
        ) + '?q=foobar'
        resp = self.client.get(url)

        self.assertEqual(302, resp.status_code)
        self.assertIn('login/?next=', resp.url)
