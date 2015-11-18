# -*- coding: utf-8 -*-
import inspect
import operator
from collections import defaultdict, Iterable

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import post_migrate
from django.utils.functional import curry
from django_extensions.db.fields.json import JSONField

from ralph.admin.helpers import get_field_by_relation_path
from ralph.attachments.models import Attachment
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.transitions.conf import TRANSITION_ATTR_TAG
from ralph.lib.transitions.exceptions import TransitionNotAllowedError
from ralph.lib.transitions.fields import TransitionField

_transitions_fields = {}


def run_field_transition(instances, transition, field, data={}, **kwargs):
    """
    Execute all actions assigned to the selected transition.
    """
    if not isinstance(instances, Iterable):
        instances = [instances]

    transition_model = instances[0].transition_models[field]
    if isinstance(transition, str):
        transition = Transition.objects.get(
            name=transition,
            model=transition_model,
        )
    for instance in instances:
        errors = defaultdict(list)
        if instance.status not in [int(s) for s in transition.source]:
            errors[instance] = 'wrong source status'
        raise TransitionNotAllowedError(
            'Transition is not allowed for '
        )
    # setattr(instance, field, int(transition.target))
    # attachment = None
    # action_names = []
    # history_kwargs = {}
    # for action in transition.actions.all():
    #     func = getattr(instance, action.name)
    #     if not func:
    #         continue
    #     defaults = {
    #         key.split('__')[1]: value
    #         for key, value in data.items()
    #         if key.startswith(action.name)
    #     }
    #     for k, v in defaults.items():
    #         value = v
    #         try:
    #             field = get_field_by_relation_path(instance, k)
    #             field_name = field.verbose_name
    #             if field.rel:
    #                 value = str(field.rel.to.objects.get(pk=v))
    #         except FieldDoesNotExist:
    #             field = func.form_fields[k]['field']
    #             if isinstance(field, forms.ChoiceField):
    #                 value = dict(field.choices).get(int(v))

    #             field_name = field.label
    #         history_kwargs[str(field_name)] = value

    #     defaults.update(kwargs)
    #     result = func(**defaults)
    #     action_names.append(func.verbose_name)

    #     if isinstance(result, Attachment):
    #         attachment = result

    # TransitionsHistory.objects.create(
    #     transition=transition,
    #     object_id=instance.pk,
    #     logged_user=kwargs['request'].user,
    #     attachment=attachment,
    #     kwargs=history_kwargs,
    #     actions=action_names
    # )
    # instance.save()
    return True, None #attachment


def get_available_transitions_for_field(instance, field):
    """
    Returns list of all available transitions for field.
    """
    if not hasattr(instance, 'transition_models'):
        return
    transitions = Transition.objects.filter(
        model=instance.transition_models[field],
    )
    return [
        transition for transition in transitions
        if instance.status in [int(s) for s in transition.source]
    ]


class TransitionWorkflowBase(ModelBase):
    """
    Added extra methods to new class based on registred transition
    fields (eg. status and etc).

    """
    def __new__(cls, name, bases, attrs):
        fields = [
            key for key, value in attrs.items()
            if issubclass(type(value), TransitionField)
        ]
        new_class = super().__new__(cls, name, bases, attrs)
        if fields:
            _transitions_fields[new_class] = fields
            for field in fields:
                new_class.add_to_class(
                    'run_{}_transition'.format(field),
                    curry(run_field_transition, field=field)
                )
                new_class.add_to_class(
                    'get_available_transitions_for_{}'.format(field),
                    curry(get_available_transitions_for_field, field=field)
                )
        return new_class


class TransitionModel(models.Model):
    content_type = models.ForeignKey(ContentType)
    field_name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('content_type', 'field_name')

    def __str__(self):
        return '{} {}'.format(self.content_type, self.field_name)


class Transition(models.Model):
    name = models.CharField(max_length=50)
    model = models.ForeignKey(TransitionModel)
    source = JSONField()
    target = models.CharField(max_length=50)
    actions = models.ManyToManyField('Action')

    class Meta:
        unique_together = ('name', 'model')

    def __str__(self):
        return self.name

    @classmethod
    def transitions_for_model(cls, model):
        content_type = ContentType.objects.get_for_model(model)
        return cls.objects.filter(model__content_type=content_type)


class Action(models.Model):
    content_type = models.ManyToManyField(ContentType)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    @classmethod
    def actions_for_model(cls, model):
        content_type = ContentType.objects.get_for_model(model)
        return cls.objects.filter(content_type=content_type)


class TransitionsHistory(TimeStampMixin):

    transition = models.ForeignKey(Transition)
    object_id = models.IntegerField(db_index=True)
    logged_user = models.ForeignKey(settings.AUTH_USER_MODEL)
    attachment = models.ForeignKey(Attachment, blank=True, null=True)
    kwargs = JSONField()
    actions = JSONField()

    def __str__(self):
        return str(self.transition)


def update_models_attrs():
    """
    Add to class new attribute `transition_models` which is dict with all
    transitionable models (key) and fields (value as list).
    """
    for model, field_names in _transitions_fields.items():
        ContentType.objects.get_for_model(model)
        content_type = ContentType.objects.get_for_model(model)
        transition_models = {}
        for field_name in field_names:
            transition_model, _ = TransitionModel.objects.get_or_create(
                content_type=content_type,
                field_name=field_name
            )
            transition_models[field_name] = transition_model
        setattr(model, 'transition_models', transition_models)


def update_transitions_affter_migrate(**kwargs):
    """
    Create or update transition for models which detetected
    TRANSITION_ATTR_TAG in any field in model.
    """
    sender_models = list(kwargs['sender'].get_models())
    getter = lambda x: operator.itemgetter(0)(x) in sender_models
    for model, field_names in filter(getter, _transitions_fields.items()):
        content_type = ContentType.objects.get_for_model(model)
        for field_name in field_names:
            transition_model, _ = TransitionModel.objects.get_or_create(
                content_type=content_type,
                field_name=field_name
            )
            detected_actions = inspect.getmembers(
                model, predicate=lambda x: hasattr(x, TRANSITION_ATTR_TAG)
            )
            for name, _ in detected_actions:
                action, _ = Action.objects.get_or_create(
                    name=name,
                )
                action.content_type.add(content_type)

post_migrate.connect(update_transitions_affter_migrate)
