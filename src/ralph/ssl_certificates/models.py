from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.assets.models.assets import Manufacturer
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin


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
    domain_ssl = models.CharField(
        verbose_name=_('domain name'),
        blank=True,
        help_text=_('Full domain name'),
        max_length=255
    )
    certificate_type = models.PositiveIntegerField(
        choices=CertificateType(),
        default=CertificateType.ov.id,
    )
    issued_by = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=False, blank=False)
    san = models.TextField(
        blank=True,
        help_text=_('All Subject Alternative Names'),
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )

    def __str__(self):
        return '{} from {} to {}'.format(
            self.name, self.date_from, self.date_to
        ) or None
