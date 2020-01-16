from dj.choices import Choice, Choices
from dj.choices.fields import ChoiceField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin


class AccessCardStatus(Choices):
    _ = Choice

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
    AdminAbsoluteUrlMixin, TimeStampMixin, Regionalizable, models.Model
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
    status = ChoiceField(
        choices=AccessCardStatus,
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
