# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib.mixins.models import TaggableMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


from ralph.security.choices import Risk, ScanStatus


class Vulnerability(
    # Regionalizable,
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        unique=True)  # mysql unique 255
    patch_deadline = models.DateTimeField(null=True, blank=True)
    risk = models.PositiveIntegerField(choices=Risk(), null=True, blank=True)
    external_vulnerability_id = models.IntegerField(
        unique=True,  # id means id
        null=True,
        blank=True,
        help_text=_('Id of vulnerability from external system'),
    )


class SecurityScan(
    # Regionalizable,
    PermByFieldMixin,
    TimeStampMixin,
    TaggableMixin,
    models.Model,
):
    last_scan_date = models.DateTimeField()
    scan_status = models.PositiveIntegerField(choices=ScanStatus())
    next_scan_date = models.DateTimeField()
    details_url = models.URLField(max_length=255, blank=True)
    rescan_url = models.URLField(blank=True, verbose_name='Rescan url')
    asset = models.ForeignKey(DataCenterAsset, null=True)
    vulnerabilities = models.ManyToManyField(Vulnerability)
