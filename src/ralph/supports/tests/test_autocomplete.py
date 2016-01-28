# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.admin.autocomplete import QUERY_PARAM
from ralph.supports.tests.factories import SupportFactory, SupportTypeFactory
from ralph.tests import RalphTestCase
from ralph.tests.mixins import ClientMixin


class SupportAutocompleteTest(TestCase, ClientMixin):

    def setUp(self):
        super().setUp()
        self.support = SupportFactory(
            name='test1',
            support_type=SupportTypeFactory(name='type1'),
            supplier='supplier1'
        )
        self.login_as_user(username='test')

    def test_autocomplete_json(self):
        client_url = reverse(
            'autocomplete-list', kwargs={
                'app': 'supports',
                'model': 'baseobjectssupport',
                'field': 'support'
            }
        )
        response = self.client.get(client_url, {QUERY_PARAM: 'test1'})

        expected_html = (
            '<strong>Date from:</strong>&nbsp;{date_from}<br>'
            '<strong>Date to:</strong>&nbsp;{date_to}<br>'
            '<strong>Asset type:</strong>&nbsp;all<br>'
            '<strong>Producer:</strong>&nbsp;{producer}<br>'
            '<strong>Supplier:</strong>&nbsp;supplier1<br>'
            '<strong>Serial no:</strong>&nbsp;{serial_no}<br>'
            '<strong>Support type:</strong>&nbsp;type1<br>'
        ).format(
            date_to=self.support.date_to,
            producer=self.support.producer,
            date_from=self.support.date_from,
            serial_no=self.support.serial_no
        )
        data = json.loads(str(response.content, 'utf-8'))['results'][0]


        self.assertEqual(
            data['label'], '{} ({}, {})'.format(
                str(self.support.name),
                self.support.date_to,
                self.support.supplier
            )
        )
        self.assertEqual(
            data['__str__'], '{} ({})'.format(
                self.support.name, self.support.date_to
            )
        )

        self.assertHTMLEqual(data['tooltip'], expected_html)
