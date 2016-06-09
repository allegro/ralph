from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_extensions.db.fields.json import JSONField

from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import TimeStampMixin
from ralph.data_importer.models import ImportedObjects as ImportedObject


def _remap_result(result):
    return {
        key: {
            'old': old,
            'new': new
        } for key, old, new in result
    }


class Run(TimeStampMixin, models.Model):
    i_am_your_father = True

    checked_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    valid_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.checked_count = self.valid_count + self.invalid_count
        super().save(*args, **kwargs)


class Result(TimeStampMixin, models.Model):
    i_am_your_father = True

    run = models.ForeignKey(Run)
    content_type = models.ForeignKey(ContentType)
    object_pk = models.IntegerField(db_index=True)

    old = models.ForeignKey(ImportedObject, null=True)
    result = JSONField()
    errors = JSONField()

    @classmethod
    def create(cls, run, obj, old, result, errors):
        if old:
            old = ImportedObject.objects.using('default').get(id=old.pk)
        opts = ContentType.objects._get_opts(obj.__class__, True)
        ct = ContentType.objects.using('default').get(
            app_label=opts.app_label, model=opts.model_name
        )
        result = _remap_result(result)
        cls.objects.create(
            run=run,
            content_type=ct,
            object_pk=obj.pk,
            old=old,
            result=result,
            errors=errors,
        )
