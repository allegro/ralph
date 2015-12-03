# -*- coding: utf-8 -*-

import inspect
import operator
from collections import defaultdict, Iterable

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.db.models.signals import post_migrate
from django.utils.functional import curry
from django_extensions.db.fields.json import JSONField

from ralph.admin.helpers import get_field_by_relation_path
from ralph.attachments.models import Attachment
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.transitions.conf import TRANSITION_ATTR_TAG
from ralph.lib.transitions.exceptions import (
    TransitionModelNotFoundError,
    TransitionNotAllowedError
)
from ralph.lib.transitions.fields import TransitionField

_transitions_fields = {}


def _generate_transition_history(
    instance, transition, user, attachment, history_kwargs, action_names, field
):
    """Return history object (without saving it) based on parameters."""
    field_value = getattr(instance, field, None)
    return TransitionsHistory(
        transition_name=transition.name,
        content_type=ContentType.objects.get_for_model(instance._meta.model),
        object_id=instance.pk,
        logged_user=user,
        attachment=attachment,
        kwargs=history_kwargs,
        actions=action_names,
        source=instance._meta.get_field(
            field
        ).choices.from_id(int(field_value)).name,
        target=instance._meta.get_field(
            field
        ).choices.from_id(int(transition.target)).name
    )


def _get_history_dict(data, instance, runned_funcs):
    history = {}
    for func in runned_funcs:
        defaults = {
            key.split('__')[1]: value
            for key, value in data.items()
            if key.startswith(func.__name__)
        }
        for k, v in defaults.items():
            value = v
            try:
                field = get_field_by_relation_path(instance, k)
                field_name = field.verbose_name
                if field.rel:
                    value = str(field.rel.to.objects.get(pk=v))
            except FieldDoesNotExist:
                field = func.form_fields[k]['field']
                if isinstance(field, forms.ChoiceField):
                    value = dict(field.choices).get(int(v))
                field_name = field.label
            history[str(field_name)] = value
    return history


def _check_type_instances(instances):
    """Function check type of instances.
    Conditions:
        - transition can run only objects with the same type.
    """
    if not all(
        map(lambda x: isinstance(instances[0], x.__class__), instances)
    ):
        raise NotImplementedError()


def _check_and_get_transition(obj, transition, field):
    """Check and get transition from parameters.

    Args:
        obj: The object from database.
        transition: The transition object or a string.
        field: The field as a string.

    Returns:
        The transition object.

    Raises:
        TransitionModelNotFoundError: An error ocurred when transition is
        not found for object's class.
    """

    if obj.__class__ not in _transitions_fields.keys():
        raise TransitionModelNotFoundError(
            'Model {} not found in registry'.format(obj.__class__)
        )
    if isinstance(transition, str):
        transition_model = obj.transition_models[field]
        transition = Transition.objects.get(
            name=transition,
            model=transition_model,
        )
    return transition


def _check_instances_for_transition(instances, transition):
    """Check in respect of the instances source status.

    Args:
        instances: Objects to checks.
        transition: The transition object or a string.

    Raises:
        TransitionNotAllowedError: An error ocurred when one or more of
        instances not allowed transition.
    """
    errors = defaultdict(list)
    for instance in instances:
        if instance.status not in [int(s) for s in transition.source]:
            errors[instance].append('wrong source status')
    if errors:
        raise TransitionNotAllowedError(
            'Transition {} is not allowed for objects'.format(transition.name),
            errors
        )


def _check_action_with_instances(instances, transition):
    for action in transition.actions.all():
        func = getattr(instances[0], action.name)
        validation_func = getattr(func, 'validation', lambda x: True)
        validation_func(instances)


@transaction.atomic
def run_field_transition(
    instances, transition_obj_or_name, field, data={}, **kwargs
):
    """
    Execute all actions assigned to the selected transition.
    """
    if not isinstance(instances, Iterable):
        instances = [instances]
    first_instance = instances[0]

    _check_type_instances(instances)
    transition = _check_and_get_transition(
        first_instance, transition_obj_or_name, field
    )
    _check_instances_for_transition(instances, transition)
    _check_action_with_instances(instances, transition)
    attachment = None
    action_names = []
    runned_funcs = []
    for action in transition.actions.all():
        func = getattr(first_instance, action.name)
        defaults = {
            key.split('__')[1]: value
            for key, value in data.items()
            if key.startswith(action.name)
        }
        defaults.update(kwargs)
        # TODO: transaction
        result = func(instances=instances, **defaults)
        runned_funcs.append(func)
        action_names.append(str(getattr(
            func,
            'verbose_name',
            func.__name__.replace('_', ' ').capitalize()
        )))
        if isinstance(result, Attachment):
            attachment = result
    history_list = []
    for instance in instances:
        setattr(instance, field, int(transition.target))
        history_kwargs = _get_history_dict(data, instance, runned_funcs)
        history_list.append(_generate_transition_history(
            instance=instance,
            transition=transition,
            user=kwargs['request'].user,
            attachment=attachment,
            history_kwargs=history_kwargs,
            action_names=action_names,
            field=field
        ))
        instance.save()
    if history_list:
        TransitionsHistory.objects.bulk_create(history_list)
    return True, attachment


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
        app_label = 'transitions'

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
        app_label = 'transitions'

    def __str__(self):
        return self.name

    @classmethod
    def transitions_for_model(cls, model):
        content_type = ContentType.objects.get_for_model(model)
        return cls.objects.filter(model__content_type=content_type)


class Action(models.Model):
    content_type = models.ManyToManyField(ContentType)
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'transitions'

    def __str__(self):
        return self.name

    @classmethod
    def actions_for_model(cls, model):
        content_type = ContentType.objects.get_for_model(model)
        return cls.objects.filter(content_type=content_type)


class TransitionsHistory(TimeStampMixin):

    content_type = models.ForeignKey(ContentType)
    transition_name = models.CharField(max_length=255)
    source = models.CharField(max_length=50, blank=True, null=True)
    target = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.IntegerField(db_index=True)
    logged_user = models.ForeignKey(settings.AUTH_USER_MODEL)
    attachment = models.ForeignKey(Attachment, blank=True, null=True)
    kwargs = JSONField()
    actions = JSONField()

    class Meta:
        app_label = 'transitions'

    def __str__(self):
        return str(self.transition_name)


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
