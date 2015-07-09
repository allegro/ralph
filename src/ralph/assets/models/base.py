# -*- coding: utf-8 -*-
from django.db import models

from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class BaseObject(PermByFieldMixin, TimeStampMixin, models.Model):

    """Base object mixin."""

    parent = models.ForeignKey('self', null=True, blank=True)
    remarks = models.TextField(blank=True)
    service_env = models.ForeignKey('ServiceEnvironment', null=True)
