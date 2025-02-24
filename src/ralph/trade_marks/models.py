# -*- coding: utf-8 -*-
from dj.choices import Choices, Country
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import AssetHolder, BaseObject
from ralph.attachments.helpers import get_file_path
from ralph.domains.models import Domain
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


def verbose_names(**kwargs):
    def wrap(cls):
        for field, value in kwargs.items():
            setattr(cls._meta.get_field(field), "verbose_name", value)
        return cls

    return wrap


def upload_dir(filename, instance):
    return get_file_path(filename, instance, default_dir="trade_marks")


class ProviderAdditionalMarking(
    AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model
):
    """
    This class is needed for additional_marking checkbox field.
    Additional_marking field is for additional services from
    trade mark register site.
    """

    pass


class TradeMarkStatus(Choices):
    _ = Choices.Choice
    application_filed = _("Application filed")
    application_refused = _("Application refused")
    application_withdrawn = _("Application withdrawn")
    application_opposed = _("Application opposed")
    registered = _("Registered")
    registration_invalidated = _("Registration invalidated")
    registration_expired = _("Registration expired")


class TradeMarkRegistrarInstitution(
    AdminAbsoluteUrlMixin, NamedMixin.NonUnique, TimeStampMixin, models.Model
):
    pass


class TradeMarkCountry(AdminAbsoluteUrlMixin, models.Model):
    country = models.PositiveIntegerField(
        verbose_name=_("trade mark country"),
        choices=Country(),
        default=Country.pl.id,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    @property
    def name(self):
        return Country.desc_from_id(self.country)


class IntellectualPropertyBase(models.Model):
    name = models.CharField(
        blank=False,
        max_length=255,
    )
    number = models.CharField(blank=False, null=False, max_length=255)
    image = models.ImageField(null=True, blank=True, upload_to=upload_dir)
    classes = models.CharField(
        blank=False,
        null=False,
        max_length=255,
    )
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_business_owner",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_technical_owner",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    order_number_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
    )
    additional_markings = models.ManyToManyField(
        ProviderAdditionalMarking,
        blank=True,
    )
    holder = models.ForeignKey(
        AssetHolder, blank=True, null=True, on_delete=models.CASCADE
    )
    status = models.PositiveIntegerField(
        choices=TradeMarkStatus(), default=TradeMarkStatus.registered.id
    )
    registrar_institution = models.ForeignKey(
        TradeMarkRegistrarInstitution, null=True, on_delete=models.CASCADE
    )
    database_link = models.URLField(
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        return "{}, {}, {} expires {}.".format(
            self.name, self.number, self.classes, self.valid_to
        )

    class Meta:
        abstract = True


class TradeMarkKind(AdminAbsoluteUrlMixin, models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255)

    def __str__(self):
        return self.type


@verbose_names(
    name=_("Trade Mark Name"),
    number=_("Trade Mark number"),
    status=_("Trade Mark status"),
    holder=_("Trade Mark holder"),
    image=_("Representation"),
)
class TradeMark(IntellectualPropertyBase, AdminAbsoluteUrlMixin, BaseObject):
    type = models.ForeignKey(
        TradeMarkKind,
        verbose_name=_("Trade Mark type"),
        related_name="trademarks",
        on_delete=models.DO_NOTHING,
        default=2,
    )
    domains = models.ManyToManyField(
        Domain,
        related_name="+",
        through="TradeMarksLinkedDomains",
    )


class TradeMarksLinkedDomains(models.Model):
    trade_mark = models.ForeignKey(TradeMark, on_delete=models.CASCADE)
    domain = models.ForeignKey(
        Domain, related_name="trade_mark", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("trade_mark", "domain")
        verbose_name = _("Trade Marks Linked Domain")
        verbose_name_plural = _("Trade Marks Linked Domains")

    def __str__(self):
        return "{} assigned to {}".format(
            self.trade_mark,
            self.domain,
        )


class TradeMarkAdditionalCountry(models.Model):
    trade_mark = models.ForeignKey(TradeMark, on_delete=models.CASCADE)
    country = models.ForeignKey(TradeMarkCountry, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Trade Mark Additional Country")
        verbose_name_plural = _("Trade Mark Additional Countries")
        unique_together = ("country", "trade_mark")


@verbose_names(
    name=_("Patent Name"),
    number=_("Patent number"),
    status=_("Patent status"),
    holder=_("Patent holder"),
    image=_("Representation"),
)
class Patent(IntellectualPropertyBase, AdminAbsoluteUrlMixin, BaseObject):
    domains = models.ManyToManyField(
        Domain,
        related_name="+",
        through="PatentsLinkedDomains",
    )


class PatentsLinkedDomains(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, related_name="patent", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("patent", "domain")
        verbose_name = _("Patent Linked Domain")
        verbose_name_plural = _("Patent Linked Domains")

    def __str__(self):
        return "{} assigned to {}".format(
            self.patent,
            self.domain,
        )


class PatentAdditionalCountry(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.CASCADE)
    country = models.ForeignKey(TradeMarkCountry, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Patent Additional Country")
        verbose_name_plural = _("Patent Additional Countries")
        unique_together = ("country", "patent")


@verbose_names(
    name=_("Design Name"),
    number=_("Design number"),
    status=_("Design status"),
    holder=_("Design holder"),
    image=_("Representation"),
)
class Design(IntellectualPropertyBase, AdminAbsoluteUrlMixin, BaseObject):
    domains = models.ManyToManyField(
        Domain,
        related_name="+",
        through="DesignsLinkedDomains",
    )


class DesignsLinkedDomains(models.Model):
    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, related_name="design", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("design", "domain")
        verbose_name = _("Design Linked Domain")
        verbose_name_plural = _("Design Linked Domains")

    def __str__(self):
        return "{} assigned to {}".format(
            self.design,
            self.domain,
        )


class DesignAdditionalCountry(models.Model):
    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    country = models.ForeignKey(TradeMarkCountry, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Design Additional Country")
        verbose_name_plural = _("Design Additional Countries")
        unique_together = ("country", "design")


@verbose_names(
    name=_("Utility Model Name"),
    number=_("Utility Model number"),
    status=_("Utility Model status"),
    holder=_("Utility Model holder"),
    image=_("Representation"),
    classes=_("IPC Classification"),
)
class UtilityModel(IntellectualPropertyBase, AdminAbsoluteUrlMixin, BaseObject):
    pass


class UtilityModelAdditionalCountry(models.Model):
    utility_model = models.ForeignKey(UtilityModel, on_delete=models.CASCADE)
    country = models.ForeignKey(TradeMarkCountry, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Utility Model Additional Country")
        verbose_name_plural = _("Utility Model Additional Countries")
        unique_together = ("country", "utility_model")


class UtilityModelLinkedDomains(models.Model):
    utility_model = models.ForeignKey(UtilityModel, on_delete=models.CASCADE)
    domain = models.ForeignKey(
        Domain, related_name="utility_model", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("utility_model", "domain")
        verbose_name = _("Utility Model Linked Domain")
        verbose_name_plural = _("Utility Model Linked Domains")

    def __str__(self):
        return "{} assigned to {}".format(
            self.utility_model,
            self.domain,
        )
