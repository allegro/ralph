# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import TimeTrackable, MACAddressField


class DHCPEntry(TimeTrackable):
    mac = MACAddressField(verbose_name=_("MAC address"), unique=False)
    ip = db.CharField(verbose_name=_("IP address"), blank=True, unique=False,
                      default="", max_length=len('xxx.xxx.xxx.xxx'))

    class Meta:
        verbose_name = _("DHCP entry")
        verbose_name_plural = _("DHCP entries")


class DHCPServer(db.Model):
    ip = db.IPAddressField(verbose_name=_("IP address"), unique=True)
    last_synchronized = db.DateTimeField(null=True)
