# -*- coding: utf-8 -*-
from django.urls import reverse

from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.mixins import ClientMixin, ReloadUrlsMixin
from ralph.tests.models import Order, OrderStatus


class TransitionAdminTest(ClientMixin, ReloadUrlsMixin, TransitionTestCase):
    def setUp(self):
        super().setUp()
        self.reload_urls()

    def test_url_for_transition(self):
        _, transition, _ = self._create_transition(Order, 'test')
        order = Order.objects.create()
        reverse(
            'admin:tests_order_transition',
            args=(order.pk, transition.pk,)
        )

    def test_should_save_attachment_url_in_session(self):
        _, transition, _ = self._create_transition(
            Order, 'packing', ['pack'], source=[OrderStatus.new.id],
            target=OrderStatus.to_send.id
        )
        order = Order.objects.create()
        transition_url = reverse(
            'admin:tests_order_transition',
            args=(order.pk, transition.pk,)
        )
        self.login_as_user()
        self.assertFalse(self.client.session.get('attachments_to_download'))
        self.client.post(transition_url)
        self.assertTrue(self.client.session.get('attachments_to_download'))

    def test_custom_template_for_transition(self):
        _, transition, _ = self._create_transition(
            Order, 'custom template test',
            template_name='test.html'
        )

    def test_success_url_should_redirect(self):
        success_url = 'http://test.com/foo/bar/'
        _, transition, _ = self._create_transition(
            Order, 'packing', ['pack'], source=[OrderStatus.new.id],
            target=OrderStatus.to_send.id,
            success_url=success_url,
        )
        order = Order.objects.create()
        transition_url = reverse(
            'admin:tests_order_transition',
            args=(order.pk, transition.pk,)
        )
        self.login_as_user()
        response = self.client.post(transition_url)
        self.assertEqual(response.url, success_url)
