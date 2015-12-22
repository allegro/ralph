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
        SupportFactory(
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
            '<strong>Date from:</strong>&nbsp;<i class="empty">'
            '&lt;empty&gt;</i><br>'
            '<strong>Date to:</strong>&nbsp;2020-12-31<br>'
            '<strong>Asset type:</strong>&nbsp;4<br>'
            '<strong>Producer:</strong>&nbsp;<i class="empty">'
            '&lt;empty&gt;</i><br>'
            '<strong>Supplier:</strong>&nbsp;supplier1<br>'
            '<strong>Serial no:</strong>&nbsp;<i class="empty">'
            '&lt;empty&gt;</i><br>'
            '<strong>Support type:</strong>&nbsp;type1<br>'
        )
        data = json.loads(str(response.content, 'utf-8'))['results'][0]

        self.assertEqual(data['label'], 'test1 (2020-12-31, supplier1)')
        self.assertEqual(data['__str__'], 'test1 (2020-12-31)')

        self.assertHTMLEqual(data['tooltip'], expected_html)
