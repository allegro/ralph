# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType

from ralph.tests import RalphTestCase
from ralph.tests.models import Order
from ralph.lib.transitions.models import TransitionConfigModel


class TransitionsTest(RalphTestCase):
    def _create_order_transition(self, name, target, source):
        TransitionConfigModel.objects.create(
            content_type=ContentType.objects.get_for_model(Order),
            name=name,
            field_name='status',
            target=target,
            source=source,
        )

    def test_setup(self):
        self._create_order_transition('release', 1, 2)
        self._create_order_transition('send', 3, 4)

        order = Order.objects.create(status=1)
        self.assertEqual(
            2,
            len(list(order._meta.get_field('status').get_all_transitions(Order)))
        )
        print(order.status)
        print([x.name for x in list(order.get_available_status_transitions())])


        order.release()  # DETELE THIS
        print(order.status)
        print([x.name for x in list(order.get_available_status_transitions())])

