# -*- coding: utf-8 -*-
from ralph.tests import RalphTestCase

from ralph.tests.models import Order


class TransitionsTest(RalphTestCase):
    def test_setup(self):
        order = Order.objects.create()
        print(
            list(order._meta.get_field('status').get_all_transitions(Order))
        )

