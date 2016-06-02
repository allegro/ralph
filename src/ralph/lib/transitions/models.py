# -*- coding: utf-8 -*-

import inspect
import logging
from collections import defaultdict

import reversion
from dj.choices import Choices
from django import forms
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
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
from ralph.lib.external_services.models import Job
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.transitions.conf import (
    DEFAULT_ASYNC_TRANSITION_SERVICE_NAME,
    TRANSITION_ATTR_TAG,
    TRANSITION_ORIGINAL_STATUS
)
from ralph.lib.transitions.exceptions import (
    TransitionModelNotFoundError,
    TransitionNotAllowedError
)
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.utils import (
    _compare_instances_types,
    _sort_graph_topologically
)

_transitions_fields = {}

logger = logging.getLogger(__name__)


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
                if isinstance(field, forms.ModelChoiceField):
                    value = str(v)
                elif isinstance(field, forms.ChoiceField):
                    value = dict(field.choices).get(int(v))
                field_name = field.label
            history[str(field_name)] = value
    return history


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
        transition: The transition object.

    Raises:
        TransitionNotAllowedError: An error ocurred when one or more of
        instances not allowed transition.
    """
    errors = defaultdict(list)
    for instance in instances:
        if instance.status not in [int(s) for s in transition.source]:
            errors[instance].append(_('wrong source status'))

    for func in transition.get_pure_actions():
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
    for func in transition.get_pure_actions():
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


def _order_actions_by_requirements(actions, instance):
    graph = _create_graph_from_actions(actions, instance)
    actions_by_name = {a.name: a for a in actions}
    for action in _sort_graph_topologically(graph):
        yield actions_by_name[action]


def run_transition(instances, transition_obj_or_name, field, data={}, **kwargs):
    """
    Main function to run transition (async or synchronous).
    """
    first_instance = instances[0]
    transition = _check_and_get_transition(
        first_instance, transition_obj_or_name, field
    )
    if transition.is_async:
        job_ids = []
        for instance in instances:
            job_id, job = TransitionJob.run(
                transition.async_service_name or DEFAULT_ASYNC_TRANSITION_SERVICE_NAME,  # noqa
                instance,
                transition=transition,
                data=data,
                **kwargs
            )
            job_ids.append(job_id)
        return job_ids
    else:
        return run_field_transition(
            instances, transition_obj_or_name, field, data, **kwargs
        )


def _prepare_action_data(
    action, data, history_kwargs=None, shared_params=None, **kwargs
):
    """
    Prepare data for single transition action

    Args:
        action: Action instance
        data: dict with
    """
    defaults = data.copy()
    defaults.update(kwargs)
    if history_kwargs is not None:
        defaults.update({'history_kwargs': history_kwargs})
    if shared_params is not None:
        defaults.update({'shared_params': shared_params})
    # for current action, strip action name from param
    # for example if current action is `test`, and it has param `abc`,
    # `test__abc` is stored in and additional param `abc` will be passed to
    # this action
    defaults.update({
        key.split('__')[1]: value
        for key, value in data.items()
        if key.startswith(action.name)
    })
    return defaults


def _save_instance_after_transition(instance, transition, user=None):
    # don't save object if any of actions have `disable_save_object` flag set
    if not any([a.disable_save_object for a in transition.get_pure_actions()]):
        with transaction.atomic(), reversion.create_revision():
            instance.save()
            # TODO: store changed fields
            reversion.set_comment('Transition {}'.format(transition))
            if user:
                reversion.set_user(user)


def _create_instance_history_entry(
    instance, transition, data, history_kwargs, user=None, attachment=None
):
    funcs = transition.get_pure_actions()
    action_names = [str(getattr(
        func,
        'verbose_name',
        func.__name__.replace('_', ' ').capitalize()
    )) for func in funcs]
    history = _get_history_dict(data, instance, funcs)
    history.update(history_kwargs.get(instance.pk, {}))
    transition_history = _generate_transition_history(
        instance=instance,
        transition=transition,
        user=user,
        attachment=attachment,
        history_kwargs=history,
        action_names=action_names,
        field=transition.model.field_name
    )
    transition_history.save()


def _post_transition_instance_processing(
    instance, transition, data, history_kwargs, user=None, attachment=None
):
    # change transition field (ex. status) if not keeping orignial
    if not int(transition.target) == TRANSITION_ORIGINAL_STATUS[0]:
        setattr(instance, transition.model.field_name, int(transition.target))
    _create_instance_history_entry(
        instance, transition, data, history_kwargs,
        user=user, attachment=attachment
    )
    _save_instance_after_transition(
        instance, transition, user
    )


@transaction.atomic
def run_field_transition(
    instances, transition_obj_or_name, field, data={}, **kwargs
):
    """
    Execute all actions assigned to the selected transition.
    """
    first_instance = instances[0]
    _compare_instances_types(instances)
    transition = _check_and_get_transition(
        first_instance, transition_obj_or_name, field
    )
    _check_instances_for_transition(instances, transition)
    _check_action_with_instances(instances, transition)
    attachment = None
    history_kwargs = defaultdict(dict)
    shared_params = defaultdict(dict)
    for action in _order_actions_by_requirements(
        transition.actions.all(), first_instance
    ):
        logger.info('Performing action {} in transition {}'.format(
            action, transition
        ))
        func = getattr(first_instance, action.name)
        defaults = _prepare_action_data(
            action,
            data,
            history_kwargs=history_kwargs,
            shared_params=shared_params,
            **kwargs
        )
        try:
            result = func(instances=instances, **defaults)
        except Exception as e:
            logger.exception(e)
            return False, None

        if isinstance(result, Attachment):
            attachment = result
    for instance in instances:
        _post_transition_instance_processing(
            instance, transition, data, history_kwargs=history_kwargs,
            user=kwargs['request'].user, attachment=attachment,
        )
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
    run_asynchronously = models.BooleanField(
        default=False,
        help_text=_(
            'Run this transition in the background (this could be enforced if '
            'you choose at least one asynchronous action)'
        )
    )
    async_service_name = models.CharField(
        max_length=100, blank=True, null=True,
        default=DEFAULT_ASYNC_TRANSITION_SERVICE_NAME, help_text=_(
            'Name of asynchronous (internal) service to run this transition. '
            'Fill this field only if you want to run this transition in the '
            'background.'
        )
    )
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

    @property
    def model_cls(self):
        return self.model.content_type.model_class()

    @property
    def is_async(self):
        return (
            self.run_asynchronously or
            any([func.is_async for func in self.get_pure_actions()])
        )

    @classmethod
    def transitions_for_model(cls, model, user=None):
        content_type = ContentType.objects.get_for_model(model)
        transitions = cls.objects.filter(model__content_type=content_type)
        return [
            transition for transition in transitions
            if _check_user_perm_for_transition(user, transition)
        ]

    def get_pure_actions(self):
        return [
            getattr(self.model_cls, action.name)
            for action in self.actions.all()
        ]

    def has_form(self):
        for action in self.get_pure_actions():
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


class TransitionJobActionStatus(Choices):
    _ = Choices.Choice

    STARTED = _('started')
    FINISHED = _('finished')
    FAILED = _('failed')


class TransitionJob(Job):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # char field to allow uids, not only ints
    object_id = models.CharField(max_length=200)
    obj = GenericForeignKey('content_type', 'object_id')
    transition = models.ForeignKey(Transition, on_delete=models.CASCADE)  # ?
    # TODO: field?

    @classmethod
    def run(
        cls, service_name, obj, transition, request=None, defaults=None,
        **kwargs
    ):
        defaults = defaults or {}
        defaults.update(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            transition=transition,
        )
        if 'data' not in kwargs:
            kwargs['data'] = {}
        for p in ['history_kwargs', 'shared_params']:
            if p not in kwargs:
                # obj.pk will be casted to str when dumping to json!
                # (json needs str as the key of an object)
                # we need to restore it in `_restore_params`
                kwargs[p] = {obj.pk: {}}
        return super().run(service_name, defaults, request=request, **kwargs)

    @classmethod
    def _restore_params(cls, obj):
        params = super()._restore_params(obj)
        # fix history_kwargs and shared_params key (from str to int)
        for param_name in ['history_kwargs', 'shared_params']:
            param = params.get(param_name, {}).copy()
            new_param = defaultdict(dict)
            for k, v in param.items():
                try:
                    k = int(k)
                except ValueError:
                    # pk is not int (ex. uid)
                    pass
                new_param[k] = v
            params[param_name] = new_param
        return params


class TransitionJobAction(TimeStampMixin):
    transition_job = models.ForeignKey(
        TransitionJob,
        on_delete=models.PROTECT,
        related_name='transition_job_actions',
    )
    action_name = models.CharField(max_length=50)
    status = models.PositiveIntegerField(
        verbose_name=_('transition action status'),
        choices=TransitionJobActionStatus(),
        default=TransitionJobActionStatus.STARTED.id,
    )
    # TODO: add retries field and max retries param for async action


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


def update_transitions_after_migrate(**kwargs):
    """
    Create or update transition for models which detetected
    TRANSITION_ATTR_TAG in any field in model.
    """
    sender_models = list(kwargs['sender'].get_models())
    action_ids = set()
    for model, field_names in _transitions_fields.items():
        if model not in sender_models:
            continue
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
                action_ids.add(action.id)
        to_delete = Action.objects.filter(content_type=content_type).exclude(
            id__in=action_ids
        )
        logger.warning('Deleting actions: {}'.format(list(to_delete)))
        to_delete.delete()

post_migrate.connect(update_transitions_after_migrate)


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
