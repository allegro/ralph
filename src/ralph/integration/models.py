# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.choices import Choices

class IntegrationType(Choices):
    _ = Choices.Choice

    custom = _("Custom")
    zabbix = _("Zabbix")


class RoleIntegration(db.Model):
    venture_role = db.ForeignKey("business.VentureRole",
                                 verbose_name=_("role"))
    type = db.PositiveIntegerField(verbose_name=_("integration type"),
                                   choices=IntegrationType(),
                                   default=IntegrationType.custom.id)
    name = db.CharField(verbose_name=_("name"), max_length=64)
    value = db.TextField(verbose_name=_("value"), blank=True, default="")

