# -*- coding: utf-8 -*-
from datetime import datetime

from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.models import TaggableMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class ScanStatus(Choices):
    _ = Choices.Choice

    ok = _("ok")
    fail = _("fail")
    error = _("error")


class Risk(Choices):
    _ = Choices.Choice

    low = _("low")
    medium = _("medium")
    high = _("high")


class Vulnerability(
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=1024,
        unique=False)
    patch_deadline = models.DateTimeField(null=True, blank=True)
    risk = models.PositiveIntegerField(choices=Risk(), null=True, blank=True)
    external_vulnerability_id = models.IntegerField(
        unique=True,  # id means id
        null=True,
        blank=True,
        help_text=_('Id of vulnerability from external system'),
    )

    @property
    def is_deadline_exceeded(self):
        return self.patch_deadline < datetime.now()


class SecurityScan(
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    last_scan_date = models.DateTimeField()
    scan_status = models.PositiveIntegerField(choices=ScanStatus())
    next_scan_date = models.DateTimeField()
    details_url = models.URLField(max_length=255, blank=True)
    rescan_url = models.URLField(blank=True, verbose_name=_('Rescan url'))
    base_object = models.ForeignKey(BaseObject)
    vulnerabilities = models.ManyToManyField(Vulnerability)
