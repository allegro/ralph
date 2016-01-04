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
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin


class SupportType(NamedMixin, models.Model):
    """The type of a support"""


class SupportStatus(Choices):
    _ = Choices.Choice

    SUPPORT = Choices.Group(0)
    new = _("new")


class Support(
    Regionalizable,
    AdminAbsoluteUrlMixin,
    NamedMixin.NonUnique,
    BaseObject,
    AutocompleteTooltipMixin
):
    asset_type = models.PositiveSmallIntegerField(
        choices=ObjectModelType(), default=ObjectModelType.all.id,
    )
    contract_id = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )
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
    serial_no = models.CharField(max_length=100, blank=True)
    invoice_no = models.CharField(max_length=100, blank=True, db_index=True)
    invoice_date = models.DateField(
        null=True, blank=True, verbose_name=_('Invoice date'),
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
    base_objects = models.ManyToManyField(
        BaseObject,
        related_name='+',
        through='BaseObjectsSupport',
    )

    autocomplete_tooltip_fields = [
        'date_from',
        'date_to',
        'asset_type',
        'producer',
        'supplier',
        'serial_no',
        'support_type'
    ]

    def __init__(self, *args, **kwargs):
        self.saving_user = None
        super(Support, self).__init__(*args, **kwargs)

    def get_natural_end_support(self):
        return naturaltime(datetime(*(self.date_to.timetuple()[:6])))

    def __str__(self):
        return '{} ({})'.format(self.name, self.date_to)

    @property
    def autocomplete_str(self):
        return '{} ({}, {})'.format(
            str(self.name), self.date_to, self.supplier
        )


class BaseObjectsSupport(models.Model):
    support = models.ForeignKey(Support)
    baseobject = BaseObjectForeignKey(
        BaseObject,
        verbose_name=_('Asset'),
        related_name='supports',
        limit_models=[
            'back_office.BackOfficeAsset',
            'data_center.DataCenterAsset'
        ]
    )

    class Meta:
        managed = False
        unique_together = ('support', 'baseobject')
        db_table = 'supports_support_base_objects'
