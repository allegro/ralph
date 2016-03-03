# -*- coding: utf-8 -*-
from dj.choices import Choices
from django.conf import settings
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.fields import TicketIdField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TaggableMixin
)


class OperationStatus(Choices):
    _ = Choices.Choice

    opened = _('open')
    in_progress = _('in progress')
    resolved = _('resolved')
    closed = _('closed')


class OperationType(MPTTModel, NamedMixin, models.Model):
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True
    )

    class choices(Choices):
        _ = Choices.Choice

        CHANGES = Choices.Group(0)
        change = _('change')

        INCIDENTS = Choices.Group(100)
        incident = _('incident')

        PROBLEMS = Choices.Group(200)
        problem = _('problem')

        FAILURES = Choices.Group(300)
        failure = _('failure')
        hardware_failure = _('hardware failure')


class Operation(AdminAbsoluteUrlMixin, TaggableMixin, models.Model):
    type = TreeForeignKey(OperationType, verbose_name=_('type'))
    title = models.CharField(
        max_length=350, null=False, blank=False, verbose_name=_('title'),
    )
    description = models.TextField(
        verbose_name=_('description'), null=True, blank=True,
    )
    status = models.PositiveIntegerField(
        verbose_name=_('status'), choices=OperationStatus(),
        default=OperationStatus.opened.id,
    )
    asignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='operations',
        verbose_name=_('asignee'),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    ticket_id = TicketIdField()
    created_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_('created date'),
    )
    update_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_('updated date'),
    )
    resolved_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_('resolved date'),
    )
    base_objects = models.ManyToManyField(
        BaseObject, related_name='operations', verbose_name=_('objects'),
        blank=True,
    )

    _operation_type_subtree = None

    @property
    def ticket_url(self):
        return '{}{}'.format(settings.ISSUE_TRACKER_URL, self.ticket_id)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        # check if operation type is in valid subtree
        if self._operation_type_subtree and self.type_id:
            type_root = OperationType.objects.get(
                pk=self._operation_type_subtree
            )
            if not self.type.is_descendant_of(type_root, include_self=True):
                raise ValidationError(
                    'Invalid Operation type. Choose descendant of {}'.format(
                        self._operation_type_subtree
                    )
                )


class OperationDescendantManager(models.Manager):
    """
    Narrow Operations only to particular type.
    """
    def __init__(self, descendants_of, *args, **kwargs):
        self._descendants_of = descendants_of
        super().__init__(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        root = OperationType.objects.get(pk=self._descendants_of)
        return queryset.filter(type__in=root.get_descendants(include_self=True))


class Change(Operation):
    objects = OperationDescendantManager(OperationType.choices.change)
    _operation_type_subtree = OperationType.choices.change

    class Meta:
        proxy = True


class Incident(Operation):
    objects = OperationDescendantManager(OperationType.choices.incident)
    _operation_type_subtree = OperationType.choices.incident

    class Meta:
        proxy = True


class Problem(Operation):
    objects = OperationDescendantManager(OperationType.choices.problem)
    _operation_type_subtree = OperationType.choices.problem

    class Meta:
        proxy = True


class Failure(Operation):
    objects = OperationDescendantManager(OperationType.choices.failure)
    _operation_type_subtree = OperationType.choices.failure

    class Meta:
        proxy = True


@receiver(post_migrate)
def rebuild_handler(sender, **kwargs):
    """
    Rebuild OperationType tree after migration of operations app.
    """
    # post_migrate is called after each app's migrations
    if sender.name == 'ralph.' + OperationType._meta.app_label:
        OperationType.objects.rebuild()
