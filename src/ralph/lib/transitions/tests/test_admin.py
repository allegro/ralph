# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.models import Order


class TransitionAdminTest(TransitionTestCase):
    def test_url_for_transition(self):
        _, transition, _ = self._create_transition(Order, 'test')
        order = Order.objects.create()
        reverse(
            'admin:tests_order_transition',
            args=(order.pk, transition.pk,)
        )
