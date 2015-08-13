# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.models.assets import Asset
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin


class Warehouse(NamedMixin, TimeStampMixin, models.Model):
    pass


class BackOfficeAsset(Regionalizable, Asset):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_owner',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_user',
    )
    location = models.CharField(max_length=128, null=True, blank=True)
    purchase_order = models.CharField(max_length=50, null=True, blank=True)
    loan_end_date = models.DateField(
        null=True, blank=True, default=None, verbose_name=_('Loan end date'),
    )

    class Meta:
        verbose_name = _('Back Office Asset')
        verbose_name_plural = _('Back Office Assets')

    @property
    def country_code(self):
        return 'PL'
