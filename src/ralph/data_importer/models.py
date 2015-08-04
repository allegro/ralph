from django.contrib.contenttypes.models import ContentType
from django.db import models

from ralph.lib.mixins.models import TimeStampMixin


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
