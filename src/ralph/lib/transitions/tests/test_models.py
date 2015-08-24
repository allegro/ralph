# -*- coding: utf-8 -*-
from ralph.lib.transitions.models import (
    Action,
    Transition,
    TransitionNotAllowedError
)
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.models import Order, OrderStatus


class TransitionsTest(TransitionTestCase):
    def test_transition_change_status(self):
        order = Order.objects.create()
        transition = Transition.objects.create(
            name='prepare', model=order.transition_models['status'],
            source=[OrderStatus.new.id],
            target=OrderStatus.to_send.id,
        )

        self.assertEqual(order.status, OrderStatus.new.id)
        order.run_status_transition(transition)
        self.assertEqual(order.status, OrderStatus.to_send.id)

    def test_run_action_during_transition(self):
        order = Order.objects.create(status=OrderStatus.to_send.id)
        transition = Transition.objects.create(
            name='send', model=order.transition_models['status'],
            source=[OrderStatus.to_send.id],
            target=OrderStatus.sended.id,
        )
        transition.actions.add(Action.objects.get(name='go_to_post_office'))

        def mocked_action(**kwargs):
            mocked_action.runned = True
        order.go_to_post_office = mocked_action
        order.run_status_transition(transition)
        self.assertTrue(mocked_action.runned)

    def test_run_transition_from_string(self):
        transition_name = 'send'
        order = Order.objects.create(status=OrderStatus.to_send.id)
        Transition.objects.create(
            name=transition_name,
            model=order.transition_models['status'],
            source=[OrderStatus.to_send.id],
            target=OrderStatus.sended.id,
        )
        self.assertTrue(order.run_status_transition(transition_name))

    def test_run_non_existent_transition(self):
        transition_name = 'non_existent_transition'
        order = Order.objects.create()
        with self.assertRaises(Transition.DoesNotExist):
            order.run_status_transition(transition_name)

    def test_available_transitions(self):
        order = Order.objects.create()
        transition = Transition.objects.create(
            name='send',
            model=order.transition_models['status'],
            source=[OrderStatus.new.id],
            target=OrderStatus.sended.id,
        )

        self.assertEqual(
            list(order.get_available_transitions_for_status()), [transition]
        )

        order.status = OrderStatus.sended.id
        self.assertEqual(
            list(order.get_available_transitions_for_status()), []
        )

    def test_forbidden_transition(self):
        order = Order.objects.create()
        transition = Transition.objects.create(
            name='send',
            model=order.transition_models['status'],
            source=[OrderStatus.to_send.id],
            target=OrderStatus.sended.id,
        )

        self.assertEqual(
            list(order.get_available_transitions_for_status()), []
        )
        with self.assertRaises(TransitionNotAllowedError):
            order.run_status_transition(transition)
