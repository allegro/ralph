# -*- coding: utf-8 -*-
import urllib

from django.test import TestCase
from django.urls import reverse

from ralph.accounts.models import RalphUser, Region
from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.admin.autocomplete import AutocompleteList


class AutocompleteSplitWordTest(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(first_name="first_name_1", last_name="last_name_1")
        UserFactory(first_name="first_name_2", last_name="last_name_2")
        self.region = RegionFactory(name="pl")
        RegionFactory(name="de")

    def test_or(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = RalphUser
        result = autocomplete_list.get_query_filters(
            RalphUser.objects.all(),
            "first_name_1 last_name_1",
            ["username", "first_name", "last_name"],
        )
        self.assertEqual(list(result), [self.user])

    def test_or_empty(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = RalphUser
        result = autocomplete_list.get_query_filters(
            RalphUser.objects.all(),
            "first_name_1 last_name_2",
            ["username", "first_name", "last_name"],
        )
        self.assertEqual(len(result), 0)

    def test_not_or(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = Region
        result = autocomplete_list.get_query_filters(
            Region.objects.all(), "pl", ["name"]
        )
        self.assertEqual(list(result), [self.region])

    def test_not_or_empty(self):
        autocomplete_list = AutocompleteList()
        autocomplete_list.model = Region
        result = autocomplete_list.get_query_filters(
            Region.objects.all(), "pl de", ["name"]
        )
        self.assertEqual(len(result), 0)

    def test_autocomplete_endpoint_required_auth(self):
        url = (
            reverse(
                "autocomplete-list",
                kwargs={"app": "assets", "field": "service_env", "model": "BaseObject"},
            )
            + "?q=foobar"
        )
        resp = self.client.get(url)

        target_params = urllib.parse.urlencode({"next": url}, safe="/")
        expected_target = reverse("admin:login") + "?{}".format(target_params)

        self.assertRedirects(resp, expected_target)
