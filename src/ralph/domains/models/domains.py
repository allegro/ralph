# -*- coding: utf-8 -*-

from dj.choices import Choices
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.assets.models.assets import AssetHolder, BusinessSegment
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.permissions import PermByFieldMixin


class DomainRegistrant(
    PermByFieldMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model,
):
    pass


class DomainStatus(Choices):
    _ = Choices.Choice

    active = _('Active')
    pending_lapse = _('Pending lapse')
    pending_transfer = _('Pending transfer away')
    lapsed = _('Lapsed (inactive)')
    transfered_away = _('Transfered away')


class Domain(BaseObject, AdminAbsoluteUrlMixin):
    name = models.CharField(
        verbose_name=_('Domain name'),
        help_text=_('Full domain name'),
        unique=True,
        max_length=255
    )
    domain_status = models.PositiveIntegerField(
        choices=DomainStatus(),
        default=DomainStatus.active.id,
    )
    business_segment = models.ForeignKey(
        BusinessSegment, blank=True, null=True,
        help_text=_("Business segment for a domain")
    )
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='domaincontract_business_owner',
        blank=True,
        null=True,
        help_text=_("Business contact person for a domain")
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='domaincontract_technical_owner',
        blank=True,
        null=True,
        help_text=_("Technical contact person for a domain")
    )
    domain_holder = models.ForeignKey(
        AssetHolder,
        blank=True,
        null=True,
        help_text=_("Company which receives invoice for the domain")
    )

    def __str__(self):
        return self.name


class DomainContract(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    TimeStampMixin,
    models.Model,
):
    domain = models.ForeignKey(Domain)
    expiration_date = models.DateField(null=True, blank=True)
    registrant = models.ForeignKey('DomainRegistrant', null=True, blank=True)
    price = models.DecimalField(
        null=True, blank=True, decimal_places=2, max_digits=15,
        help_text=_("Price for domain renewal for given period"),
        verbose_name=_("Price"))

    def __str__(self):
        return "{domain_name} - {expiration_date}".format(
            domain_name=self.domain.name,
            expiration_date=self.expiration_date
        )
        return self.hostname
