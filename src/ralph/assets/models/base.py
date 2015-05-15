# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models

from ralph.assets.models.mixins import TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class BaseObject(PermByFieldMixin, TimeStampMixin, models.Model):

    """Base object mixin."""

    parent = models.ForeignKey('self')
    remarks = models.TextField(blank=True)
    service_env = models.ForeignKey('ServiceEnvironment')
