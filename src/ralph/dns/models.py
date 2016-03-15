# -*- coding: utf-8 -*-
from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.data_center.models.physical import DataCenterAsset


class RecordType(Choices):
    _ = Choices.Choice

    a = _('A')
    txt = _('TXT')
    cname = _('CNAME')


class DNSRecord(models.Model):

    data_center_asset = models.ForeignKey(DataCenterAsset)
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text=_("Actual name of a record. Must not end in a '.' and be"
                    " fully qualified - it is not relative to the name of the"
                    " domain!"),
    )
    type = models.IntegerField(
        choices=RecordType(), help_text=_("Record type"),
    )
    content = models.CharField(
        max_length=255, blank=True, null=True,
        help_text=_("The 'right hand side' of a DNS record. For an A"
                    " record, this is the IP address"),
    )
    ptr = models.BooleanField(default=False)

    class Meta:
        managed = False
