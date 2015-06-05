# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible

from ralph.assets.models.mixins import TimeStampMixin


@python_2_unicode_compatible
class ImportedObjects(TimeStampMixin, models.Model):

    """Django models for imported objects."""

    content_type = models.ForeignKey(ContentType)
    object_pk = models.IntegerField(db_index=True)
    old_object_pk = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return "{} - {}".format(
            self.content_type.app_label,
            self.content_type.model
        )
