# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.lib.transitions.forms import TransitionForm
from ralph.lib.transitions.models import (
    Action,
    Transition,
    TransitionModel,
)
from ralph.tests.models import Order


class TransitionTestCaseMixin(object):
    def _get_form(self, obj=None):
        class Form(TransitionForm):
            if obj:
                _transition_model_instance = obj
        return Form

    def _create_transition(
        self, model, name, actions=None, field='status',
        source=None, target=None, **kwargs
    ):
        transition_model = TransitionModel.get_for_field(model, field)
        transition_kwargs = dict(name=name, model=transition_model, **kwargs)
        if source:
            transition_kwargs['source'] = source
        if target:
            transition_kwargs['target'] = target
        transition = Transition.objects.create(**transition_kwargs)
        order_ct = ContentType.objects.get_for_model(Order)
        actions_query_kwargs = {'content_type': order_ct}
        if actions:
            actions_query_kwargs = {'name__in': actions}
            actions = Action.objects.filter(**actions_query_kwargs)
        else:
            actions = Action.actions_for_model(model)
        transition.actions.add(*[x for x in actions])
        return transition_model, transition, actions


class TransitionTestCase(TransitionTestCaseMixin, TestCase):
    pass
