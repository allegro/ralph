# -*- coding: utf-8 -*-
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models

from ralph.lib.mixins.models import TimeStampMixin


class ImportedObjectDoesNotExist(Exception):
    pass


class ImportedObjects(TimeStampMixin, models.Model):
    """Django models for imported objects."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_pk = models.IntegerField(db_index=True)
    old_object_pk = models.CharField(max_length=255, db_index=True)
    old_ci_uid = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    object = fields.GenericForeignKey("content_type", "object_pk")

    def __str__(self):
        return "{} - {}".format(self.content_type.app_label, self.content_type.model)

    class Meta:
        unique_together = [
            ("content_type", "object_pk"),
            ("content_type", "old_object_pk"),
        ]

    @classmethod
    def get_object_from_old_pk(cls, model, old_pk):
        """
        Return object based on old ID.
        """
        try:
            imported_obj = cls.objects.get(
                old_object_pk=old_pk,
                content_type=ContentType.objects.get_for_model(model),
            )
        except cls.DoesNotExist:
            raise ImportedObjectDoesNotExist()
        else:
            try:
                return model.objects.get(id=imported_obj.object_pk)
            except model.DoesNotExist:
                raise ImportedObjectDoesNotExist(
                    "Target object does not exist (it was probably removed)"
                )

    @classmethod
    def create(cls, obj, old_pk):
        """
        Create new imported object

        Args:
            obj: Django Model Object
            old_pk: Old primary key

        Returns:
            ImportedObjects instance
        """
        return cls.objects.create(
            content_type=ContentType.objects.get_for_model(obj._meta.model),
            object_pk=obj.pk,
            old_object_pk=old_pk,
        )

    @classmethod
    def get_imported_id(cls, obj):
        """
        Return old object primary key for given object.

        Args:
            obj: Django object model

        Returns:
            Return old object primary key
        """
        try:
            imported_obj = cls.objects.get(
                object_pk=obj.pk,
                content_type=ContentType.objects.get_for_model(obj._meta.model),
            )
        except cls.DoesNotExist:
            raise ImportedObjectDoesNotExist()
        else:
            return imported_obj.old_object_pk
