# -*- coding: utf-8 -*-
from dj.choices import Choices
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
    wf = _('Word - Figurative')


class ProviderAdditionalMarking(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model
):
    pass


class TradeMarkStatus(Choices):
    _ = Choices.Choice
    af = _('Application filed')
    ar = _('Application refused')
    aw = _('Application withdrawn')
    ao = _('Application opposed')
    registered = _('Registered')
    ri = _('Registration invalidated')
    re = _('Registration expired')


class TradeMarks(AdminAbsoluteUrlMixin, BaseObject, Regionalizable):
    registrant_number = models.CharField(
        verbose_name=_('Registrant number'),
        blank=False,
        null=False,
        max_length=255
    )
    tm_type = models.PositiveIntegerField(
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
    date_to = models.DateField(null=False, blank=False)
    name = models.CharField(
        verbose_name=_('Trade Mark name'),
        blank=False,
        max_length=255,
    )
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
    tm_holder = models.ForeignKey(
        AssetHolder,
        verbose_name=_('Trade Mark holder'),
        blank=True,
        null=True
    )
    tm_status = models.PositiveIntegerField(
        verbose_name=_('Trade Mark status'),
        choices=TradeMarkStatus(),
        default=TradeMarkStatus.registered.id
    )
    domain = models.ManyToManyField(
        Domain,
        related_name='+',
        through='TradeMarksLinkedDomains',
    )

    def __str__(self):
        return '{} ({})'.format(
            self.name, self.date_to
        ) or None


class TradeMarksLinkedDomains(models.Model):
    tm_name = models.ForeignKey(TradeMarks)
    domain = models.ForeignKey(
        Domain,
        related_name='tm_name'
    )

    class Meta:
        unique_together = ('tm_name', 'domain')

    def __str__(self):
        return '{} assigned to {}'.format(
            self.tm_name, self.domain,
        )
