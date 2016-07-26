from django.db import models
from django.conf import settings


class SoftDeletableManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(deleted=False)
        return qs


class SoftDeletable(models.Model):
    deleted = models.BooleanField()
    objects = SoftDeletableManager()

    class Meta:
        abstract = True


class Ralph2LinkMixin(object):
    def get_link_to_r2(self):
        url = '/'.join(self._meta.db_table.split('_'))
        return '/'.join([
            settings.RALPH2_PREVIEW_PREFIX_URL, url, str(self.pk)
        ])


def generate_meta(app_label, model_name):
    class Meta:
        managed = False
        db_table = '_'.join([app_label, model_name]).lower()
    return Meta
