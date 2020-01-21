from functools import partial

from dj.choices import Choices
from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.back_office.models import autocomplete_user
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions


class AccessCardStatus(Choices):
    _ = Choices.Choice

    new = _('new')
    in_progress = _('in progress')
    lost = _('lost')
    damaged = _('damaged')
    used = _('in use')
    free = _('free')
    return_in_progress = _('return in progres')
    liquidated = _('liquidated')


class AccessZone(AdminAbsoluteUrlMixin, MPTTModel, models.Model):
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'parent']

    def __str__(self):
        return self.name

    description = models.TextField(
        null=True,
        blank=True,
        help_text=_('Optional description')
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True
    )


class AccessCard(
    AdminAbsoluteUrlMixin,
    TimeStampMixin,
    Regionalizable,
    models.Model,
    metaclass=TransitionWorkflowBaseWithPermissions
):
    visual_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Number visible on the access card')
    )
    system_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Internal number in the access system')
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date of issue to the User')
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_('Optional notes')
    )
    user = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=_('User of the card'),
        on_delete=models.SET_NULL
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=('Owner of the card'),
        on_delete=models.SET_NULL
    )
    status = TransitionField(
        choices=AccessCardStatus(),
        default=AccessCardStatus.new.id,
        null=False,
        blank=False,
        help_text=_('Access card status')
    )
    access_zones = TreeManyToManyField(
        AccessZone,
        blank=True,
        related_name='access_cards'
    )

    def __str__(self):
        return _('Access Card: {}').format(self.visual_number)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(
            status=AccessCardStatus.liquidated.id
        )

    @classmethod
    @transition_action()
    def unassign_user(cls, instances, **kwargs):
        for instance in instances:
            kwargs['history_kwargs'][instance.pk][
                'affected_user'
            ] = str(instance.user)
            instance.user = None

    @classmethod
    @transition_action(
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user',
                'default_value': partial(autocomplete_user, field_name='user')
            }
        },
    )
    def assign_user(cls, instances, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs['user']))
        for instance in instances:
            instance.user = user

    @classmethod
    @transition_action(
        form_fields={
            'owner': {
                'field': forms.CharField(label=_('Owner')),
                'autocomplete_field': 'owner',
                'default_value': partial(autocomplete_user, field_name='owner')
            }
        },
        help_text=_('assign owner'),
    )
    def assign_owner(cls, instances, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs['owner']))
        for instance in instances:
            instance.owner = owner

    @classmethod
    @transition_action()
    def unassign_owner(cls, instances, **kwargs):
        for instance in instances:
            kwargs['history_kwargs'][instance.pk][
                'affected_owner'
            ] = str(instance.owner)
            instance.owner = None
