# -*- coding: utf-8 -*-
from datetime import datetime

from dj.choices import Choices
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.assets.models.assets import AssetHolder, BudgetInfo
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ObjectModelType
from ralph.lib.mixins.fields import BaseObjectForeignKey
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    PriceMixin
)
from ralph.lib.polymorphic.fields import PolymorphicManyToManyField
from ralph.lib.polymorphic.models import PolymorphicQuerySet


class SupportType(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    """The type of a support"""


class SupportStatus(Choices):
    _ = Choices.Choice

    SUPPORT = Choices.Group(0)
    new = _("new")


SUPPORTS_RELATED_OBJECTS_PREFETCH_RELATED = [
    # prefetch all baseobjects related with support; this allows to call
    # [bos.base_object for bos in support.baseobjectssupport_set.all()]
    # without additional queries
    models.Prefetch(
        "baseobjectssupport_set__baseobject",
        # polymorphic manager is used to get final instance of the object
        # (ex. DataCenterAsset)
        queryset=BaseObject.polymorphic_objects.all(),
    )
]


class AssignedObjectsCountManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(assigned_objects_count=models.Count("base_objects"))
        )


class SupportsRelatedObjectsManager(AssignedObjectsCountManager):
    """
    Prefetch related objects by-default
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(*SUPPORTS_RELATED_OBJECTS_PREFETCH_RELATED)
        )


class Support(
    Regionalizable,
    AdminAbsoluteUrlMixin,
    NamedMixin.NonUnique,
    PriceMixin,
    BaseObject,
    AutocompleteTooltipMixin,
):
    _allow_in_dashboard = True

    asset_type = models.PositiveSmallIntegerField(
        choices=ObjectModelType(),
        default=ObjectModelType.all.id,
    )
    contract_id = models.CharField(
        verbose_name=_("contract ID"), max_length=50, blank=False
    )
    description = models.CharField(max_length=100, blank=True)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=False, blank=False)
    escalation_path = models.CharField(max_length=200, blank=True)
    contract_terms = models.TextField(blank=True)
    sla_type = models.CharField(max_length=200, blank=True)
    status = models.PositiveSmallIntegerField(
        default=SupportStatus.new.id,
        verbose_name=_("status"),
        choices=SupportStatus(),
        null=False,
        blank=False,
    )
    producer = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=100, blank=True)
    serial_no = models.CharField(
        verbose_name=_("serial number"), max_length=100, blank=True
    )
    invoice_no = models.CharField(
        verbose_name=_("invoice number"), max_length=100, blank=True, db_index=True
    )
    invoice_date = models.DateField(
        verbose_name=_("invoice date"), null=True, blank=True
    )
    period_in_months = models.IntegerField(null=True, blank=True)
    property_of = models.ForeignKey(
        AssetHolder,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    budget_info = models.ForeignKey(
        BudgetInfo,
        blank=True,
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )
    support_type = models.ForeignKey(
        SupportType,
        on_delete=models.PROTECT,
        blank=True,
        default=None,
        null=True,
    )
    base_objects = PolymorphicManyToManyField(
        BaseObject,
        related_name="+",
        through="BaseObjectsSupport",
    )

    autocomplete_tooltip_fields = [
        "date_from",
        "date_to",
        "asset_type",
        "producer",
        "supplier",
        "serial_no",
        "support_type",
    ]

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    # automatically prefetch related objects
    objects_with_related = SupportsRelatedObjectsManager()

    def __init__(self, *args, **kwargs):
        self.saving_user = None
        super(Support, self).__init__(*args, **kwargs)

    def get_natural_end_support(self):
        return naturaltime(datetime(*(self.date_to.timetuple()[:6])))

    def __str__(self):
        return "{} ({})".format(self.name, self.date_to)

    @property
    def autocomplete_str(self):
        return "{} ({}, {})".format(str(self.name), self.date_to, self.supplier)


class BaseObjectsSupport(AdminAbsoluteUrlMixin, models.Model):
    support = models.ForeignKey(Support, on_delete=models.CASCADE)
    baseobject = BaseObjectForeignKey(
        BaseObject,
        verbose_name=_("Asset"),
        related_name="supports",
        limit_models=["back_office.BackOfficeAsset", "data_center.DataCenterAsset"],
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("support", "baseobject")
