# -*- coding: utf-8 -*-
from ralph.lib.transitions.models import TRANSITION_ORIGINAL_STATUS
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.models import Order, OrderStatus


class TransitionFormTest(TransitionTestCase):
    def test_raise_error_when_instance_is_empty(self):
        with self.assertRaises(ValueError):
            self._get_form()()

    def test_raise_error_when_instance_is_incorrect(self):
        class IncorrectObject(object):
            pass
        with self.assertRaises(TypeError):
            self._get_form(IncorrectObject())()

    def test_action_choices(self):
        transition_model, transition, actions = self._create_transition(
            Order, 'test'
        )
        form = self._get_form(transition_model)(instance=transition)
        self.assertCountEqual(
            [x[1] for x in form.fields['actions'].widget.choices],
            [getattr(Order, a.name).verbose_name for a in actions]
        )

    def test_source_choices(self):
        transition_model, transition, actions = self._create_transition(
            Order, 'test'
        )
        form = self._get_form(transition_model)(instance=transition)
        self.assertCountEqual(
            [x[1] for x in form.fields['source'].choices],
            [s.name for s in OrderStatus.__choices__]
        )

    def test_target_choices(self):
        transition_model, transition, actions = self._create_transition(
            Order, 'test'
        )
        form = self._get_form(transition_model)(instance=transition)
        order_status = [s.name for s in OrderStatus.__choices__]
        self.assertCountEqual(
            [x[1] for x in form.fields['target'].choices[1:]],
            order_status + [TRANSITION_ORIGINAL_STATUS[1]]
        )

    def test_should_pass_when_user_checked_two_or_more_actions_with_attachment(self):  # noqa
        transition_model, transition, actions = self._create_transition(
            Order, 'test'
        )
        data = {
            'name': 'test',
            'model': transition_model,
            'source': [OrderStatus.new.id],
            'target': OrderStatus.sended.id,
            'actions': list(actions.values_list('id', flat=True))
        }
        form = self._get_form(transition_model)(data, instance=transition)
        self.assertTrue(form.is_valid())
