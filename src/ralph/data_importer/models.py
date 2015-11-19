# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models

from ralph.lib.mixins.models import TimeStampMixin


class ImportedObjectDoesNotExist(Exception):
    pass


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

    @classmethod
    def get_object_from_old_pk(cls, model, old_pk):
        """
        Return object based on old ID.
        """
        try:
            imported_obj = cls.objects.get(
                old_object_pk=old_pk,
                content_type=ContentType.objects.get_for_model(model)
            )
        except cls.DoesNotExist:
            raise ImportedObjectDoesNotExist()
        else:
            return model.objects.get(id=imported_obj.object_pk)

    @classmethod
    def get_imported_id(cls, obj):
        """
        Return old object primary key for given object.
        """
        try:
            imported_obj = cls.objects.get(
                object_pk=obj.pk,
                content_type=ContentType.objects.get_for_model(obj._meta.model)
            )
        except cls.DoesNotExist:
            raise ImportedObjectDoesNotExist()
        else:
            return imported_obj.old_object_pk
