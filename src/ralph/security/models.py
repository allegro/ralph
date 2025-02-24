# -*- coding: utf-8 -*-
from datetime import datetime

from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    TaggableMixin,
    TimeStampMixin
)
from ralph.lib.permissions.models import PermByFieldMixin


def any_exceeded(vulnerabilties):
    return any([v.is_deadline_exceeded for v in vulnerabilties])


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
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    _allow_in_dashboard = True

    name = models.CharField(verbose_name=_("name"), max_length=1024, unique=False)
    display_name = models.CharField(verbose_name=_("display name"), max_length=1024)
    patch_deadline = models.DateTimeField(null=True, blank=True)
    risk = models.PositiveIntegerField(choices=Risk(), null=True, blank=True)
    external_vulnerability_id = models.IntegerField(
        unique=True,  # id means id
        null=True,
        blank=True,
        help_text=_("Id of vulnerability from external system"),
    )

    @property
    def is_deadline_exceeded(self):
        return self.patch_deadline < datetime.now()

    def __str__(self):
        deadline = (
            self.patch_deadline.strftime("%Y-%m-%d") if self.patch_deadline else "-"
        )
        return "{} ({})".format(self.name, deadline)


class SecurityScan(
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    _allow_in_dashboard = True

    last_scan_date = models.DateTimeField()
    scan_status = models.PositiveIntegerField(choices=ScanStatus())
    next_scan_date = models.DateTimeField()
    details_url = models.URLField(max_length=255, blank=True)
    rescan_url = models.URLField(blank=True, verbose_name=_("Rescan url"))
    base_object = models.OneToOneField(
        BaseObject,
        on_delete=models.CASCADE,
    )
    vulnerabilities = models.ManyToManyField(Vulnerability, blank=True)
    # this is a quirk field, it is updated manually (for now it's in API)
    # this is because it's hard to handling it automatically
    # (its value is computed depending on M2M field and M2M signals are
    # complicated)
    is_patched = models.BooleanField(default=False)

    @property
    def is_ok(self):
        return self.scan_status == ScanStatus.ok.id

    def update_is_patched(self):
        """Updates `is_patched` field depending on vulnerabilities"""
        self.is_patched = not any_exceeded(self.vulnerabilities.all())

    def __str__(self):
        return "{} {} ({})".format(
            self.last_scan_date.strftime("%Y-%m-%d"),
            ScanStatus.from_id(self.scan_status).desc,
            self.base_object.content_type,
        )
