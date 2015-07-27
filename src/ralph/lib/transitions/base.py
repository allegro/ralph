from collections import namedtuple

from django.utils.functional import curry
from django.db import models
from django.db.models.base import ModelBase

from django_fsm import transition


import logging
logger = logging.getLogger(__name__)

TransitionConfigItem = namedtuple(
    'TransitionConfigItem', 'source target actions name'
)

from ralph.assets.models.choices import AssetStatus

configs = {
    'status': [
        TransitionConfigItem(
            source=1,
            target=AssetStatus.in_progress.id,
            actions=['preparation', 'assign_user'],
            name='dupa',
        ),
    ]
}


# from ralph.lib.transitions.models import TransitionConfigModel


class WorkflowBase(ModelBase):
    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)

        if not new_class._meta.abstract:
            for field_name, trans_configs in configs.items():
                for config in trans_configs:
                    model_field = new_class._meta.get_field(field_name)
                    new_transition = transition(
                        field=model_field,
                        source=config.source,
                        target=config.target,
                    )
                    trans_func = curry(
                        new_class.actions_dispatcher, actions=config.actions
                    )
                    trans_func.__name__ = config.name
                    trans_func = new_transition(trans_func)
                    setattr(new_class, config.name, trans_func)
                model_field._collect_transitions(sender=new_class)
        return new_class

    def actions_dispatcher(self, *args, **kwargs):
        actions = kwargs.pop('actions')
        for action in actions:
            func = getattr(self, action, None)
            if not func:
                continue
            func(*args, **kwargs)


class StandardWorkflowMixin(models.Model, metaclass=WorkflowBase):

    def preparation(self, *args, **kwargs):
        print('preparation')  # DETELE THIS

    def assign_user(self, *args, **kwargs):
        print('assign_user')  # DETELE THIS

    class Meta:
        abstract = True
