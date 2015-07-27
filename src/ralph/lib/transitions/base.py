from collections import namedtuple

from django.utils.functional import curry
from django.db import models
from django.db.models.base import ModelBase

from django_fsm import transition


import logging
logger = logging.getLogger(__name__)

TransitionConfigItem = namedtuple(
    'TransitionConfigItem', 'source target actions name field_name'
)

from ralph.assets.models.choices import AssetStatus


configs = [
    TransitionConfigItem(
        source=AssetStatus.new.id,
        target=AssetStatus.used.id,
        actions=[],
        name='release',
        field_name='status',
    ),
    TransitionConfigItem(
        source=AssetStatus.used.id,
        target=AssetStatus.damaged.id,
        actions=[],
        name='recyckling',
        field_name='status',
    ),
    TransitionConfigItem(
        source='*',
        target=AssetStatus.damaged.id,
        actions=[],
        name='recyckling',
        field_name='status',
    ),
]


from ralph.lib.transitions.models import TransitionConfigModel


def modify_class(klass):
    # if not getattr(klass, '_transitions_configured', False):
    #     return
    if not klass._meta.abstract:
        # print(DataCenter.objects.all())
        # configs = TransitionConfigModel.objects.all()
        for config in configs:
            model_field = klass._meta.get_field(config.field_name)
            new_transition = transition(
                field=model_field,
                source=config.source,
                target=config.target,
            )
            trans_func = curry(
                klass.actions_dispatcher, actions=config.actions
            )
            trans_func.__name__ = config.name
            trans_func = new_transition(trans_func)
            setattr(klass, config.name, trans_func)
        model_field._collect_transitions(sender=klass)
        setattr(klass, '_transitions_configured', True)


class WorkflowBase(ModelBase):
    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)
        # modify_class(new_class)
        return new_class



# class StandardWorkflowMixin(models.Model, metaclass=WorkflowBase):
class StandardWorkflowMixin(models.Model):
    def actions_dispatcher(self, *args, **kwargs):
        actions = kwargs.pop('actions')
        for action in actions:
            func = getattr(self, action, None)
            if not func:
                continue
            func(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        modify_class(self.__class__)
        super().__init__(*args, **kwargs)

    def preparation(self, *args, **kwargs):
        print('preparation')  # DETELE THIS

    def assign_user(self, *args, **kwargs):
        print('assign_user')  # DETELE THIS

    class Meta:
        abstract = True
