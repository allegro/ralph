from collections import namedtuple

from django.utils.functional import curry
from django.db import models

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
        target=AssetStatus.in_progress.id,
        actions=[],
        name='release',
        field_name='status',
    ),
    TransitionConfigItem(
        source=AssetStatus.in_progress.id,
        target=AssetStatus.used.id,
        actions=[],
        name='to user',
        field_name='status',
    ),
    TransitionConfigItem(
        source=[AssetStatus.new.id, AssetStatus.used.id],
        target=AssetStatus.loan.id,
        actions=[],
        name='loan',
        field_name='status',
    ),
    TransitionConfigItem(
        source=[AssetStatus.loan.id],
        target=AssetStatus.new.id,
        actions=[],
        name='return asset',
        field_name='status',
    ),
    TransitionConfigItem(
        source=AssetStatus.damaged.id,
        target=AssetStatus.liquidated.id,
        actions=[],
        name='liquid',
        field_name='status',
    ),
]


from ralph.lib.transitions.models import TransitionConfigModel
import logging
logger = logging.getLogger(__name__)


class WorkflowMixin(models.Model):
    def actions_dispatcher(self, *args, **kwargs):
        actions = kwargs.pop('actions')
        for action in actions:
            func = getattr(self, action, None)
            if not func:
                continue
            func(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        klass = self.__class__
        if not klass._meta.abstract:
            configs = TransitionConfigModel.objects.all()
            for config in configs:
                normalized_name = config.name.replace(' ', '_')
                model_field = klass._meta.get_field(config.field_name)
                new_transition = transition(
                    field=model_field,
                    source=config.source and int(config.source) or '*',
                    target=int(config.target),
                )
                trans_func = curry(
                    klass.actions_dispatcher, actions=config.actions
                )
                trans_func.__name__ = normalized_name
                trans_func = new_transition(trans_func)
                setattr(klass, normalized_name, trans_func)
                model_field._collect_transitions(sender=klass)

    def preparation(self, *args, **kwargs):
        print('preparation')  # DETELE THIS

    def assign_user(self, *args, **kwargs):
        print('assign_user')  # DETELE THIS

    class Meta:
        abstract = True
