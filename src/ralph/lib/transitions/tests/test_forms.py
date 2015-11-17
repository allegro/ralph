# -*- coding: utf-8 -*-
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
            [x[1] for x in form.fields['actions'].choices],
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
        self.assertCountEqual(
            [x[1] for x in form.fields['target'].choices[1:]],
            [s.name for s in OrderStatus.__choices__]
        )

    def test_should_raise_vaild_error_when_user_checked_two_or_more_actions_with_attachemnt(self):  # noqa
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
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'actions': [
                'Please select at most one action which return attachment.'
            ]
        })
