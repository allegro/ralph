# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import Asset
from ralph.assets.models.mixins import (
    NamedMixin,
    TimeStampMixin
)


class Warehouse(NamedMixin, TimeStampMixin, models.Model):
    pass


class BackOfficeAsset(Asset):
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

    class Meta:
        verbose_name = _('Back Office Asset')
        verbose_name_plural = _('BO Assets')

    @property
    def country_code(self):
        return 'PL'
