# -*- coding: utf-8 -*-
from datetime import datetime

from dj.choices import Choices
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.models import NamedMixin, TaggableMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class SupportType(NamedMixin, models.Model):
    """The type of a support"""


class SupportStatus(Choices):
    _ = Choices.Choice

    SUPPORT = Choices.Group(0)
    new = _("new")


class Support(
    Regionalizable,
    PermByFieldMixin,
    NamedMixin.NonUnique,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    contract_id = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=100, blank=True)
    # TODO: new attachment mechanism
    # attachments = models.ManyToManyField(
    #     models_assets.Attachment, null=True, blank=True
    # )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=False, blank=False)
    escalation_path = models.CharField(max_length=200, blank=True)
    contract_terms = models.CharField(max_length=200, blank=True)
    remarks = models.TextField(blank=True)
    sla_type = models.CharField(max_length=200, blank=True)
    # asset_type = models.PositiveSmallIntegerField(
    #     choices=AssetType()
    # )
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
    # property_of = models.ForeignKey(
    #     AssetOwner,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    # )
    support_type = models.ForeignKey(
        SupportType,
        on_delete=models.PROTECT,
        blank=True,
        default=None,
        null=True,
    )
    base_objects = models.ManyToManyField(BaseObject, related_name='supports')

    def __init__(self, *args, **kwargs):
        self.saving_user = None
        super(Support, self).__init__(*args, **kwargs)

    def get_natural_end_support(self):
        return naturaltime(datetime(*(self.date_to.timetuple()[:6])))
