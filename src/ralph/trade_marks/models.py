# -*- coding: utf-8 -*-
from dj.choices import Choices, Country
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import AssetHolder, BaseObject
from ralph.attachments.helpers import get_file_path
from ralph.domains.models import Domain
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


def upload_dir(filename, instance):
    return get_file_path(
        filename, instance, default_dir="trade_marks"
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


class TradeMarkRegistrarInstitution(
    AdminAbsoluteUrlMixin,
    NamedMixin.NonUnique,
    TimeStampMixin,
    models.Model
):
    pass


class TradeMarkCountry(
    AdminAbsoluteUrlMixin,
    models.Model
):
    country = models.PositiveIntegerField(
        verbose_name=_('trade mark country'),
        choices=Country(),
        default=Country.pl.id,
        null=True,
        blank=True
    )

    def __str__(self):
        return Country.desc_from_id(self.country)


class TradeMark(AdminAbsoluteUrlMixin, BaseObject):
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
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=upload_dir
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
    registrar_institution = models.ForeignKey(
        TradeMarkRegistrarInstitution,
        null=True,
    )

    def __str__(self):
        return '{}, {}, {} expires {}.'.format(
            self.name, self.registrant_number,
            self.registrant_class, self.valid_to
        )

    def image_tag(self):
        if not self.image:
            return ""
        return mark_safe(
            '<img src="%s" width="150" />' % self.image.url
        )

    image_tag.short_description = _('Image')
    image_tag.allow_tags = True


class TradeMarksLinkedDomains(models.Model):
    trade_mark = models.ForeignKey(TradeMark)
    domain = models.ForeignKey(
        Domain,
        related_name='trade_mark'
    )

    class Meta:
        unique_together = ('trade_mark', 'domain')
        verbose_name = _('Trade Marks Linked Domain')
        verbose_name_plural = _('Trade Marks Linked Domains')

    def __str__(self):
        return '{} assigned to {}'.format(
            self.trade_mark, self.domain,
        )


class TradeMarkAdditionalCountry(models.Model):
    trade_mark = models.ForeignKey(TradeMark)
    country = models.ForeignKey(TradeMarkCountry)

    class Meta:
        verbose_name = _('Trade Mark Additional Country')
        verbose_name_plural = _('Trade Mark Additional Countries')
        unique_together = ('country', 'trade_mark')
