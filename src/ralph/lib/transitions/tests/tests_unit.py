# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType

from ralph.tests import RalphTestCase
from ralph.tests.models import Order
from ralph.lib.transitions.models import TransitionConfigModel


class TransitionsTest(RalphTestCase):
    def test_setup(self):
        TransitionConfigModel.objects.create(
            content_type=ContentType.objects.get_for_model(Order),
            name='dupa',
            field_name='status',
            target=1,
            source=2,
        )
        TransitionConfigModel.objects.create(
            content_type=ContentType.objects.get_for_model(Order),
            name='dupa_123',
            field_name='status',
            target=3,
            source=4,
        )
        [Order.objects.create() for _ in range(10)]
        order = Order.objects.create()
        print(
            [x.name for x in order._meta.get_field('status').get_all_transitions(Order)]
        )
        self.assertEqual(
            4,
            len(list(order._meta.get_field('status').get_all_transitions(Order)))
        )

        order.dupa()  # DETELE THIS
        self.assertEqual(order.status, 2)
        order.dupa_123()  # DETELE THIS
        self.assertEqual(order.status, 3)

