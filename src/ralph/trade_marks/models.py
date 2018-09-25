# -*- coding: utf-8 -*-
from dj.choices import Choices, Country
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.models import AssetHolder, BaseObject
from ralph.domains.models import Domain
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


class TradeMarkType(Choices):
    _ = Choices.Choice
    word = _('Word')
    figurative = _('Figurative')
    word_figurative = _('Word - Figurative')


class ProviderAdditionalMarking(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model
):
    """
    This class is needed for additional_marking checkbox field.
    Additional_marking field is for additional services from
    trade mark register site.
    """
    pass


class TradeMarkStatus(Choices):
    _ = Choices.Choice
    application_filed = _('Application filed')
    application_refused = _('Application refused')
    application_withdrawn = _('Application withdrawn')
    application_opposed = _('Application opposed')
    registered = _('Registered')
    registration_invalidated = _('Registration invalidated')
    registration_expired = _('Registration expired')


class TradeMark(Regionalizable, AdminAbsoluteUrlMixin, BaseObject):
    name = models.CharField(
        verbose_name=_('Trade Mark name'),
        blank=False,
        max_length=255,
    )
    registrant_number = models.CharField(
        verbose_name=_('Registrant number'),
        blank=False,
        null=False,
        max_length=255
    )
    type = models.PositiveIntegerField(
        verbose_name=_('Trade Mark type'),
        choices=TradeMarkType(),
        default=TradeMarkType.figurative.id
    )
    registrant_class = models.CharField(
        verbose_name=_('Registrant class'),
        blank=False,
        null=False,
        max_length=255,
    )
    valid_to = models.DateField(null=False, blank=False)
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='trademark_business_owner',
        blank=False,
        null=False
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='trademark_technical_owner',
        blank=False,
        null=False
    )
    order_number_url = models.URLField(
        max_length=255, blank=True, null=True,
    )
    additional_markings = models.ManyToManyField(
        ProviderAdditionalMarking,
        blank=True,
    )
    holder = models.ForeignKey(
        AssetHolder,
        verbose_name=_('Trade Mark holder'),
        blank=True,
        null=True
    )
    status = models.PositiveIntegerField(
        verbose_name=_('Trade Mark status'),
        choices=TradeMarkStatus(),
        default=TradeMarkStatus.registered.id
    )
    domains = models.ManyToManyField(
        Domain,
        related_name='+',
        through='TradeMarksLinkedDomains',
    )


class TradeMarksLinkedDomains(models.Model):
    trade_mark = models.ForeignKey(TradeMark)
    domain = models.ForeignKey(
        Domain,
        related_name='trade_mark'
    )

    class Meta:
        unique_together = ('trade_mark', 'domain')

    def __str__(self):
        return '{} assigned to {}'.format(
            self.trade_mark, self.domain,
        )
