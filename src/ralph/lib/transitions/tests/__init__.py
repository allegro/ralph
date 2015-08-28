# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.lib.transitions.forms import TransitionForm
from ralph.lib.transitions.models import (
    Action,
    Transition,
    update_models_attrs,
)

from ralph.tests.models import Order


class TransitionTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        update_models_attrs()

    def _get_form(self, obj=None):
        class Form(TransitionForm):
            if obj:
                _transition_model_instance = obj
        return Form

    def _create_transition(
        self, model, name, actions=None, field='status'
    ):
        transition_model = model.transition_models[field]
        transition = Transition.objects.create(
            name=name, model=transition_model
        )
        order_ct = ContentType.objects.get_for_model(Order)
        actions_query_kwargs = {'content_type': order_ct}
        if actions:
            actions_query_kwargs = {'name__in': actions}
        actions = Action.objects.filter(**actions_query_kwargs)
        transition.actions.add(*[x for x in actions])
        return transition_model, transition, actions
