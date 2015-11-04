# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.mixins import ReloadUrlsMixin
from ralph.tests.models import Order


class TransitionAdminTest(ReloadUrlsMixin, TransitionTestCase):
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
