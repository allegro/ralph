from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.assets.models.assets import Manufacturer
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, PriceMixin


class CertificateType(Choices):
    _ = Choices.Choice

    ev = _("EV")
    ov = _("OV")
    dv = _("DV")
    wildcard = _("Wildcard")
    multisan = _("Multisan")
    internal = _("CA ENT")


class SSLCertificate(AdminAbsoluteUrlMixin, PriceMixin, BaseObject):
    name = models.CharField(
        verbose_name=_("certificate name"),
        help_text=_("Full certificate name"),
        max_length=255,
    )
    domain_ssl = models.CharField(
        verbose_name=_("domain name"),
        blank=True,
        help_text=_("Full domain name"),
        max_length=255,
    )
    certificate_type = models.PositiveIntegerField(
        choices=CertificateType(),
        default=CertificateType.ov.id,
    )
    certificate_repository = models.CharField(
        verbose_name=_("certificate repository"),
        blank=True,
        help_text=_("Certificate source repository"),
        max_length=255,
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
        help_text=_("All Subject Alternative Names"),
    )

    def __str__(self):
        return (
            "{} from {} to {}".format(self.name, self.date_from, self.date_to) or None
        )
