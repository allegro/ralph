from six import with_metaclass
from django_fsm import transition, FSMIntegerField
from django.utils.functional import curry
from functools import partial
from collections import namedtuple

from django.db import models
from django.db.models.base import ModelBase

TransitionConfigItem = namedtuple(
    'TransitionConfigItem', 'source target actions name'
)

from ralph.assets.models.choices import AssetStatus

configs = [
    TransitionConfigItem(
        source=[AssetStatus.new.id],
        target=AssetStatus.in_progress.id,
        actions=['preparation', 'assign_user'],
        name='dupa',
    ),
]


class WorkflowBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        return new_class


class StandardWorkflowMixin(with_metaclass(WorkflowBase, models.Model)):

    def preparation(self):
        print('dupa')  # DETELE THIS

    def assign_user(self):
        print('assign_user')  # DETELE THIS

    def actions_dispatcher(self, actions_to_run, *args, **kwargs):
        print(self, args, kwargs)  # DETELE THIS
        print(actions_to_run)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_name = 'status'
        for config in configs:
            new_transition = transition(
                field=self._meta.get_field(field_name),
                source=config.source,
                target=config.target,
            )
            func_name = '_action_{}_{}'.format(config.name, '_'.join(config.actions))
            new_dispatcher = curry(self.actions_dispatcher, config.actions)
            setattr(self, func_name, curry(new_transition(new_dispatcher), self))
            # new_func = transition()


# class StandardWorkflowMixin(object):
