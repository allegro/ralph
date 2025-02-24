# -*- coding: utf-8 -*-
import json

from django.test import TestCase
from django.urls import reverse

from ralph.admin.autocomplete import QUERY_PARAM
from ralph.supports.tests.factories import SupportFactory, SupportTypeFactory
from ralph.tests.mixins import ClientMixin


class SupportAutocompleteTest(TestCase, ClientMixin):
    def setUp(self):
        super().setUp()
        self.support = SupportFactory(
            name="test1",
            support_type=SupportTypeFactory(name="type1"),
            supplier="supplier1",
        )
        self.login_as_user(username="test")

    def test_autocomplete_json(self):
        client_url = reverse(
            "autocomplete-list",
            kwargs={
                "app": "supports",
                "model": "baseobjectssupport",
                "field": "support",
            },
        )
        response = self.client.get(client_url, {QUERY_PARAM: "test1"})

        expected_html = (
            "Date from: {date_from}\n"
            "Date to: {date_to}\n"
            "Asset type: all\n"
            "Producer: {producer}\n"
            "Supplier: supplier1\n"
            "Serial number: {serial_no}\n"
            "Support type: type1\n"
        ).format(
            date_to=self.support.date_to,
            producer=self.support.producer,
            date_from=self.support.date_from,
            serial_no=self.support.serial_no,
        )
        data = json.loads(str(response.content, "utf-8"))["results"][0]

        self.assertEqual(
            data["__str__"],
            "{} ({}, {})".format(
                str(self.support.name), self.support.date_to, self.support.supplier
            ),
        )

        self.assertHTMLEqual(data["tooltip"], expected_html)
