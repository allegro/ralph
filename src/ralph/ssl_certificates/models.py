# -*- coding: utf-8 -*-

from dj.choices import Choices
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.assets.models.assets import AssetHolder
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class CertificateType(Choices):
    _ = Choices.Choice

    ev = _('EV')
    ov = _('OV')
    dv = _('DV')
    wildcard = _('Wildcard')
    multisan = _('Multisan')
    internal = _('CA ENT')


class SSLCertificate(AdminAbsoluteUrlMixin, BaseObject):
    name = models.CharField(
        verbose_name=_('certificate name'),
        help_text=_('Full certificate name'),
        max_length=255
    )
    certificate_type = models.PositiveIntegerField(
        choices=CertificateType(),
        default=CertificateType.ov.id,
    )
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='certificates_business_owner',
        blank=True,
        null=True,
        help_text=_("Business contact person for a certificate")
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='certificates_technical_owner',
        blank=True,
        null=True,
        help_text=_("Technical contact person for a certificate")
    )
    issued_by = models.ForeignKey(
        AssetHolder,
        blank=True,
        null=True,
        help_text=_("Company which receives certificate")
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=False, blank=False)
    san = models.TextField(
        blank=True,
        help_text=_("All Subject Alternative Name"),
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )
