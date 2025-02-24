# -*- coding: utf-8 -*-

from dj.choices import Choices
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.assets.models.assets import AssetHolder, BusinessSegment
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    PriceMixin,
    TimeStampMixin
)
from ralph.lib.permissions.models import PermByFieldMixin


class DomainRegistrant(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model,
):
    pass


class DomainStatus(Choices):
    _ = Choices.Choice

    active = _("Active")
    pending_lapse = _("Pending lapse")
    pending_transfer = _("Pending transfer away")
    lapsed = _("Lapsed (inactive)")
    transfered_away = _("Transfered away")


class WebsiteType(Choices):
    _ = Choices.Choice

    none = _("None")
    redirect = _("Redirect")
    direct = _("Direct")


class DomainType(Choices):
    _ = Choices.Choice

    business = _("Business")
    business_security = _("Business security")
    technical = _("Technical")


class DomainCategory(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model,
):
    pass


class DNSProvider(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model,
):
    pass


class DomainProviderAdditionalServices(
    AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model
):
    pass


class Domain(BaseObject, AdminAbsoluteUrlMixin, models.Model):
    name = models.CharField(
        verbose_name=_("domain name"),
        help_text=_("Full domain name"),
        unique=True,
        max_length=255,
    )
    domain_status = models.PositiveIntegerField(
        choices=DomainStatus(),
        default=DomainStatus.active.id,
    )
    business_segment = models.ForeignKey(
        BusinessSegment,
        blank=True,
        null=True,
        help_text=_("Business segment for a domain"),
        on_delete=models.CASCADE,
    )
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="domaincontract_business_owner",
        blank=True,
        null=True,
        help_text=_("Business contact person for a domain"),
        on_delete=models.CASCADE,
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="domaincontract_technical_owner",
        blank=True,
        null=True,
        help_text=_("Technical contact person for a domain"),
        on_delete=models.CASCADE,
    )
    domain_holder = models.ForeignKey(
        AssetHolder,
        blank=True,
        null=True,
        help_text=_("Company which receives invoice for the domain"),
        on_delete=models.CASCADE,
    )
    domain_type = models.PositiveIntegerField(
        default=DomainType.business.id,
        choices=DomainType(),
    )
    website_type = models.PositiveIntegerField(
        default=WebsiteType.direct.id,
        choices=WebsiteType(),
        help_text=_("Type of website which domain refers to."),
    )
    website_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Website url which website type refers to."),
    )
    domain_category = models.ForeignKey(
        DomainCategory, blank=True, null=True, on_delete=models.CASCADE
    )
    dns_provider = models.ForeignKey(
        DNSProvider,
        blank=True,
        null=True,
        help_text=_("Provider which keeps domain's DNS"),
        on_delete=models.CASCADE,
    )
    additional_services = models.ManyToManyField(
        DomainProviderAdditionalServices,
        blank=True,
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.website_type == WebsiteType.none.id and self.website_url:
            raise ValidationError(
                {"website_url": _("Website url should be empty for this website type")}
            )
        elif self.website_type == WebsiteType.redirect.id and not self.website_url:
            raise ValidationError(
                {"website_url": _("Website url should be filled for this website type")}
            )


class DomainContract(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    TimeStampMixin,
    PriceMixin,
    models.Model,
):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    expiration_date = models.DateField(null=True, blank=True)
    registrant = models.ForeignKey(
        "DomainRegistrant", null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "{domain_name} - {expiration_date}".format(
            domain_name=self.domain.name, expiration_date=self.expiration_date
        )
