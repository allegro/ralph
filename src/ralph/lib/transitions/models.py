# -*- coding: utf-8 -*-

import inspect
import logging
import operator
from collections import defaultdict

import reversion
from django import forms
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.db.models.signals import (
    post_delete,
    post_migrate,
    post_save,
    pre_save
)
from django.dispatch import receiver
from django.utils.functional import curry
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField

from ralph.admin.helpers import (
    get_content_type_for_model,
    get_field_by_relation_path
)
from ralph.attachments.models import Attachment
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.transitions.conf import TRANSITION_ATTR_TAG
from ralph.lib.transitions.exceptions import (
    TransitionModelNotFoundError,
    TransitionNotAllowedError
)
from ralph.lib.transitions.fields import TransitionField

_transitions_fields = {}

logger = logging.getLogger(__name__)


TRANSITION_ORIGINAL_STATUS = (0, 'Keep orginal status')


class CycleError(Exception):
    pass


def _generate_transition_history(
    instance, transition, user, attachment, history_kwargs, action_names, field
):
    """Return history object (without saving it) based on parameters."""
    field_value = getattr(instance, field, None)
    try:
        target = instance._meta.get_field(
            field
        ).choices.from_id(int(transition.target)).name
    except ValueError:
        target = None

    try:
        source = instance._meta.get_field(
            field
        ).choices.from_id(int(field_value)).name
    except ValueError:
        source = None

    return TransitionsHistory(
        transition_name=transition.name,
        content_type=get_content_type_for_model(instance._meta.model),
        object_id=instance.pk,
        logged_user=user,
        attachment=attachment,
        kwargs=history_kwargs,
        actions=action_names,
        source=source,
        target=target
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
            if func.form_fields[k].get('exclude_from_history', False):
                continue
            value = v
            try:
                field = get_field_by_relation_path(instance, k)
                if isinstance(field, models.ForeignKey):
                    value = str(field.rel.to.objects.get(pk=v))
                    field_name = field.verbose_name
                elif isinstance(field, models.ManyToOneRel):
                    value = ', '.join(map(str, v))
                    field_name = v.model._meta.verbose_name_plural
                else:
                    field_name = field.verbose_name
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
            errors[instance].append(_('wrong source status'))

    for func in transition.get_pure_actions(instances[0]):
        error = func.precondition(instances)
        if error:
            for instance, error_details in error.items():
                errors[instance].append(error_details)

    if errors:
        raise TransitionNotAllowedError(
            'Transition {} is not allowed for objects'.format(transition.name),
            errors
        )


def _check_action_with_instances(instances, transition):
    for func in transition.get_pure_actions(instances[0]):
        validation_func = getattr(func, 'validation', lambda x: True)
        validation_func(instances)


def _check_user_perm_for_transition(user, transition):
    if not user:
        return True
    return user.has_perm('{}.{}'.format(
        transition.permission_info['content_type'].app_label,
        transition.permission_info['codename']
    ))


def _create_graph_from_actions(actions, instance):
    graph = {}
    actions_set = set()
    for action in actions:
        actions_set.add(action.name)
        func = getattr(instance, action.name)
        graph.setdefault(action.name, [])
        for requirement in getattr(func, 'run_after', []):
            graph.setdefault(requirement, []).append(action.name)
    return {k: v for (k, v) in graph.items() if k in actions_set}


def _sort_graph_topologically(graph):
    # calculate input degree (number of nodes pointing to particular node)
    indeg = {k: 0 for k in graph}
    for node, edges in graph.items():
        for edge in edges:
            indeg[edge] += 1
    # sort graph topologically
    # return nodes which input degree is 0
    no_requirements = set([a for a in indeg if indeg.get(a, 0) == 0])
    while no_requirements:
        action_name = no_requirements.pop()
        # for each node to which this one is pointing - decrease input degree
        for dependency in graph[action_name]:
            indeg[dependency] -= 1
            # add to set of nodes ready to be returned (without nodes pointing
            # to it)
            if indeg[dependency] == 0:
                no_requirements.add(dependency)
        yield action_name
    if any(indeg.values()):
        raise CycleError("Cycle detected during topological sort")


def _order_actions_by_requirements(actions, instance):
    graph = _create_graph_from_actions(actions, instance)
    actions_by_name = {a.name: a for a in actions}
    for action in _sort_graph_topologically(graph):
        yield actions_by_name[action]


@transaction.atomic
def run_field_transition(
    instances, transition_obj_or_name, field, data={}, **kwargs
):
    """
    Execute all actions assigned to the selected transition.
    """
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
    func_history_kwargs = defaultdict(dict)
    disable_save_object = False
    for action in _order_actions_by_requirements(
        transition.actions.all(), first_instance
    ):
        logger.info('Performing action {} in transition {}'.format(
            action, transition
        ))
        func = getattr(first_instance, action.name)
        if func.disable_save_object:
            disable_save_object = True
        defaults = data.copy()
        defaults.update(kwargs)
        defaults.update({'history_kwargs': func_history_kwargs})
        defaults.update({
            key.split('__')[1]: value
            for key, value in data.items()
            if key.startswith(action.name)
        })
        try:
            result = func(instances=instances, **defaults)
        except Exception as e:
            logger.exception(e)
            return False, None

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
        if not int(transition.target) == TRANSITION_ORIGINAL_STATUS[0]:
            setattr(instance, field, int(transition.target))
        history_kwargs = _get_history_dict(data, instance, runned_funcs)
        history_kwargs.update(func_history_kwargs[instance.pk])
        history_list.append(_generate_transition_history(
            instance=instance,
            transition=transition,
            user=kwargs['request'].user,
            attachment=attachment,
            history_kwargs=history_kwargs,
            action_names=action_names,
            field=field
        ))
        if not disable_save_object:
            with transaction.atomic(), reversion.create_revision():
                instance.save()
                reversion.set_comment('Transition {}'.format(transition))
                reversion.set_user(kwargs['request'].user)
    if history_list:
        TransitionsHistory.objects.bulk_create(history_list)
    return True, attachment


def get_available_transitions_for_field(instance, field, user=None):
    """
    Returns list of all available transitions for field.
    """
    if not hasattr(instance, 'transition_models'):
        return []
    transitions = Transition.objects.filter(
        model=instance.transition_models[field],
    )
    result = []
    for transition in transitions:
        # check if source field value is in values available for this transition
        # and if user has rights to execute this transition
        if (
            getattr(instance, field) in [int(s) for s in transition.source] and
            _check_user_perm_for_transition(user, transition)
        ):
            result.append(transition)
    return result


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

    @property
    def permission_info(self):
        return {
            'name': 'Can run {} transition'.format(self.name.lower()),
            'content_type': self.model.content_type,
            'codename': 'can_run_{}_transition'.format(slugify(self.name))
        }

    @classmethod
    def transitions_for_model(cls, model, user=None):
        content_type = ContentType.objects.get_for_model(model)
        transitions = cls.objects.filter(model__content_type=content_type)
        return [
            transition for transition in transitions
            if _check_user_perm_for_transition(user, transition)
        ]

    def get_pure_actions(self, instance):
        return [
            getattr(instance, action.name) for action in self.actions.all()
        ]

    def has_form(self, instance):
        for action in self.get_pure_actions(instance):
            if getattr(action, 'form_fields', None):
                return True
        return False


class Action(models.Model):
    content_type = models.ManyToManyField(ContentType)
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'transitions'
        ordering = ['name']

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

    for model, field_names in filter(
        lambda x: operator.itemgetter(0)(x) in sender_models,
        _transitions_fields.items()
    ):
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


@receiver(post_delete, sender=Transition)
def post_delete_transition(sender, instance, **kwargs):
    Permission.objects.filter(**instance.permission_info).delete()


@receiver(pre_save, sender=Transition)
def post_save_transition(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:  # raised ex. during fixtures loading
            pass
        else:
            setattr(instance, '_old_permission_info', old.permission_info)


@receiver(post_save, sender=Transition)
def create_permission(sender, instance, created, **kwargs):
    if created:
        Permission.objects.create(**instance.permission_info)
    else:
        old_info = getattr(instance, '_old_permission_info', None)
        if not old_info:
            return
        perm, created = Permission.objects.get_or_create(**old_info)
        if not created:
            Permission.objects.filter(pk=perm.pk).update(
                **instance.permission_info
            )
