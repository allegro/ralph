from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_extensions.db.fields.json import JSONField

from ralph.data_importer.models import ImportedObjects as ImportedObject
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin


def _remap_result(result):
    return {
        key: {
            'old': old,
            'new': new
        } for key, old, new in result
    }


class CrossValidationRun(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    i_am_your_father = True

    checked_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    valid_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return 'Run {}'.format(self.modified)

    def save(self, *args, **kwargs):
        self.checked_count = self.valid_count + self.invalid_count
        super().save(*args, **kwargs)


class CrossValidationResult(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    i_am_your_father = True

    run = models.ForeignKey(CrossValidationRun)
    content_type = models.ForeignKey(ContentType)
    object_pk = models.IntegerField(db_index=True, null=True)
    object = generic.GenericForeignKey('content_type', 'object_pk')

    old = models.ForeignKey(ImportedObject, null=True)
    diff = JSONField()
    errors = JSONField()

    @classmethod
    def create(cls, run, obj, old, diff, errors):
        if old:
            old = ImportedObject.objects.using('default').get(id=old.pk)
        opts = ContentType.objects._get_opts(obj.__class__, True)
        ct = ContentType.objects.using('default').get(
            app_label=opts.app_label, model=opts.model_name
        )
        if diff:
            diff = _remap_result(diff)
        cls.objects.create(
            run=run,
            content_type=ct,
            object_pk=obj.pk,
            old=old,
            diff=diff,
            errors=errors,
        )

    @classmethod
    def get_last_diff(cls, obj):
        opts = obj._meta
        latest_run = CrossValidationRun.objects.order_by('-created').first()
        if not latest_run:
            return None
        ct = ContentType.objects.using('default').get(
            app_label=opts.app_label, model=opts.model_name
        )
        return cls.objects.filter(
            run=latest_run, content_type=ct, object_pk=obj.pk
        ).first()
