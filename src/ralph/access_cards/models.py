from dj.choices import Choice, Choices
from dj.choices.fields import ChoiceField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser
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


class AccessCard(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
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
        related_name='used_access_cards',
        help_text=_('User of the card')
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='owned_access_cards',
        help_text=_('Owner of the card')
    )
    status = ChoiceField(
        choices=AccessCardStatus,
        default=AccessCardStatus.new.id,
        null=False,
        blank=False,
        help_text=_('Access card status')
    )
    def __str__(self):
        return _('Access Card: {}').format(self.visual_number)
